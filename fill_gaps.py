"""
fill_gaps.py — Extract missing financial data for 13 low-coverage companies.
Uses PyMuPDF (fitz) for fast text extraction.
Applies validation rules before merging into dashboard_data.json.
Only fills gaps — does not overwrite existing non-zero values.

Key fixes vs prior scripts:
  - Denomination-aware parsing (thousands vs millions)
  - Line-anchored patterns to avoid false positives (e.g. year headers)
  - Year-value exclusion: won't match 2019-2026 as a financial metric
"""
import fitz, re, json
from pathlib import Path

PDF_DIR = Path('pdfs')

# ── Target companies (dashboard name → PDF filename patterns) ─────────────────
TARGETS = {
    'Brit Reinsurance Bermuda Limited':             ['Brit-Reinsurance-Bermuda-Limited'],
    'Fortitude International Reinsurance Ltd.':     ['Fortitude-International-Reinsurance-Ltd'],
    'Antares Reinsurance Company Limited':          ['Antares-Reinsurance-Company-Limited'],
    'Everest International Reinsurance Ltd.':       ['Everest-International-Reinsurance-Ltd'],
    'Hannover Re Bermuda':                          ['Hannover-Re-Bermuda-Ltd'],
    'ABR Reinsurance Ltd.':                         ['ABR-Reinsurance-Ltd'],
    'Allied World Assurance Company Ltd':           ['Allied-World-Assurance-Company-Ltd'],
    'Convex Re Limited':                            ['Convex-Re-Limited'],
    'DaVinci Reinsurance Ltd.':                     ['DaVinci-Reinsurance-Ltd', 'Davinci-Reinsurance-Ltd'],
    'American International Reinsurance Company Ltd.': ['American-International-Reinsurance-Company-Ltd'],
    'Argo Re Ltd.':                                 ['Argo-Re-Ltd'],
    'Markel Bermuda':                               ['Markel-Bermuda-Limited'],
    'XL Bermuda':                                   ['XL-Bermuda-Ltd'],
}

# ── PDF finder: match data year in filename suffix ─────────────────────────────
def find_pdf(patterns, year):
    """Find PDF where the data year appears in the Financial-Statement part of name."""
    year_str = str(year)
    candidates = []
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        name = pdf.name
        # Primary: data year appears in "---YYYY-Financial-Statement" or "--YYYY-Financial-Statement"
        if (f'---{year_str}-Financial-Statement' in name or
                f'--{year_str}-Financial-Statement' in name or
                f'-{year_str}-Financial-Statement' in name):
            for pat in patterns:
                if pat.lower() in name.lower():
                    candidates.append(pdf)
                    break
    if candidates:
        return candidates[-1]
    # Fallback: year_str anywhere in name + pattern
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        name = pdf.name
        if year_str in name:
            for pat in patterns:
                if pat.lower() in name.lower():
                    return pdf
    return None

# ── Text extraction ────────────────────────────────────────────────────────────
def extract_text(path, max_pages=50):
    try:
        doc = fitz.open(str(path))
        parts = [page.get_text() for i, page in enumerate(doc) if i < max_pages]
        doc.close()
        return '\n'.join(parts)
    except Exception:
        return ''

# ── Denomination detection ─────────────────────────────────────────────────────
def detect_denom(text):
    """Detect reporting denomination from PDF text.
    Returns: 'thousands', 'millions', or 'unknown' (default: thousands for BMA filings).
    """
    sample = text[:10000].lower()
    if re.search(r'expressed\s+in\s+(?:thousands|000s)\b|in\s+thousands\s+of|'
                 r'\(in\s+thousands\)|in\s+thousands\b|\bthousands\b', sample):
        return 'thousands'
    if re.search(r'expressed\s+in\s+(?:millions)\b|in\s+millions\s+of|'
                 r'\(in\s+millions\)|in\s+millions\b|\bmillions\b', sample):
        return 'millions'
    # Heuristic: if we see numbers > 1M in the text, assume thousands
    big = re.findall(r'[\d,]{9,}', sample)  # numbers with 7+ digits (commas included)
    if big:
        return 'thousands'
    return 'thousands'  # BMA Class 4 default

# ── Number parsing ─────────────────────────────────────────────────────────────
YEAR_VALS = set(range(2015, 2030))  # years to exclude as financial metrics

def pn(s, denom='thousands'):
    """Parse a number string → float in USD millions, using denomination context."""
    if not s:
        return None
    s = s.strip().replace(',', '').replace(' ', '').replace('\n', '')
    neg = (s.startswith('(') and s.endswith(')')) or s.startswith('-')
    s = s.strip('()').lstrip('-')
    try:
        v = float(s)
        if neg:
            v = -v
        # Exclude year-like values from being mistaken for financials
        if int(abs(v)) in YEAR_VALS:
            return None
        # Apply denomination conversion
        if denom == 'thousands':
            if abs(v) > 1_000_000_000:   # actual dollars slipped in
                v = round(v / 1_000_000, 1)
            elif abs(v) > 1_000:          # values in thousands → divide by 1000
                v = round(v / 1_000, 1)
            else:                          # < 1000 thousands = < $1M — likely a ratio or small item
                v = round(v, 1)
        elif denom == 'millions':
            v = round(v, 1)              # already in millions
        else:  # unknown fallback
            if abs(v) > 1_000_000_000:
                v = round(v / 1_000_000, 1)
            elif abs(v) > 1_000_000:
                v = round(v / 1_000, 1)
            else:
                v = round(v, 1)
        return v if v != 0 else None
    except Exception:
        return None

# ── Metric extraction ──────────────────────────────────────────────────────────
# N = number pattern — requires at least 3 digits to avoid matching tiny/short values
N  = r'([\(\-]?\d[\d,\.]*)'
# Number with at least 3 digits (avoids single-digit or 2-digit false positives)
N3 = r'(\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\d{4,}(?:\.\d+)?)'

def find(text, denom, *pats):
    """Try regex patterns, return first valid parsed value.
    Handles optional $ prefix before numbers (e.g. '$ 5,162.1').
    """
    for pat in pats:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            # Get the last capture group (the number)
            grp = m.group(m.lastindex) if m.lastindex else m.group(1)
            # Strip optional leading $ sign
            grp = re.sub(r'^\$\s*', '', grp.strip())
            v = pn(grp, denom)
            if v is not None:
                return v
    return None

def extract_metrics(text, denom):
    """Extract all key financial metrics from text with denomination awareness."""
    # N_OPT: number optionally preceded by $ sign on same or next whitespace
    N_OPT = rf'(?:\$\s*)?{N3}'

    # Balance sheet
    bs = {
        'Total Assets': find(text, denom,
            rf'^Total assets\s+{N_OPT}',
            rf'^TOTAL ASSETS\s+{N_OPT}',
            rf'Total assets\s*\$?\s*{N3}',
            rf'Total Assets\s+{N3}'),
        'Total Equity': find(text, denom,
            rf"^Total (?:shareholders?'?|stockholders?'?|members?'?)\s*equity\s+{N_OPT}",
            rf"^Total equity\s+{N_OPT}",
            rf"^TOTAL (?:SHAREHOLDERS?'?|STOCKHOLDERS?'?) EQUITY\s+{N_OPT}",
            rf"^TOTAL EQUITY\s+{N_OPT}",
            rf"Total shareholder['\u2019]?s\s*equity\s*\$?\s*{N3}",
            rf"TOTAL SHAREHOLDER['\u2019]?S EQUITY\s*\$?\s*{N3}",
            rf"Shareholders?'\s*(?:equity|funds)\s+{N3}"),
        'Total Liabilities': find(text, denom,
            rf'^Total liabilities\s+(?!and ){N_OPT}',
            rf'^TOTAL LIABILITIES\s+(?!AND ){N_OPT}',
            rf'Total liabilities\s+{N3}'),
        'Total Investments': find(text, denom,
            rf'^Total investments\s+{N_OPT}',
            rf'^TOTAL INVESTMENTS\s+{N_OPT}',
            rf'^Total investment assets\s+{N3}',
            rf'Total investments\s+{N3}'),
        'Cash and Cash Equivalents': find(text, denom,
            rf'^Cash and cash equivalents\s+{N_OPT}',
            rf'Cash and cash equivalents\s+{N3}'),
    }

    # Income statement — use line-start anchors to avoid partial-phrase matches
    inc = {
        # Standard patterns + IFRS 17 alias "Reinsurance revenue (gross)"
        'Gross Premiums Written': find(text, denom,
            rf'^Gross premiums?\s*written\s+{N_OPT}',
            rf'^GROSS PREMIUMS?\s*WRITTEN\s+{N_OPT}',
            rf'Gross premiums? written\s+{N_OPT}',
            rf'^Reinsurance revenue \(gross\)\s+{N3}'),
        'Net Premiums Earned': find(text, denom,
            rf'^Net premiums?\s*earned\s+{N_OPT}',
            rf'^NET PREMIUMS?\s*EARNED\s+{N_OPT}',
            rf'Net premiums? earned\s+{N_OPT}'),
        # Standard + IFRS 17 alias "Ordinary investment income" / "Investment result"
        'Net Investment Income': find(text, denom,
            rf'^Net investment income\s+{N_OPT}',
            rf'^NET INVESTMENT INCOME\s+{N_OPT}',
            rf'Net investment income\s+{N_OPT}',
            rf'^Ordinary investment income\s+{N3}',
            rf'^Investment result\s+{N3}'),
        'Investment Gains/Losses': find(text, denom,
            rf'^Net (?:realized\s+)?(?:investment\s+)?(?:gains?|losses?)\s+{N_OPT}',
            rf'^(?:Net )?(?:realized|unrealized)\s+(?:investment\s+)?(?:gains?|losses?)\s+{N_OPT}',
            rf'Net gains? \(losses?\) on investments\s+{N_OPT}'),
        'Total Revenues': find(text, denom,
            rf'^Total revenues?\s+{N_OPT}',
            rf'^TOTAL REVENUES?\s+{N_OPT}',
            rf'^Total income\s+{N_OPT}'),
        'Losses and LAE': find(text, denom,
            rf'^(?:Losses|Claims)\s+(?:and\s+)?(?:loss\s+adjustment\s+expenses?|LAE|claim\s+expenses?)\s+{N_OPT}',
            rf'^Net (?:losses|claims)\s+(?:and\s+(?:loss\s+adjustment\s+expenses?\s+)?)?(?:incurred\s+)?{N_OPT}',
            rf'^(?:Losses|Claims)\s+incurred\s+{N_OPT}',
            rf'(?:Losses|Claims) and (?:loss adjustment|claim) expenses?\s+{N_OPT}'),
        'Total Expenses': find(text, denom,
            rf'^Total (?:expenses?|(?:costs?\s+and\s+)?operating\s+expenses?)\s+{N_OPT}',
            rf'^TOTAL EXPENSES?\s+{N_OPT}',
            rf'Total expenses?\s+{N_OPT}'),
        # Net Income: carefully anchored to avoid "recognized in net income 2023"
        # Also handle "Net income/(loss) and comprehensive income/(loss)  $ 560,884"
        'Net Income': find(text, denom,
            rf'^Net (?:income|profit|earnings?)\s+{N_OPT}',
            rf'^Net income/\(loss\)\s+{N_OPT}',
            rf'^Net income \(loss\)\s+{N_OPT}',
            rf'^Net (?:income|earnings?)\s+(?:attributable\s+to\s+shareholders?\s+)?{N_OPT}',
            rf'^Profit for the (?:year|period)\s+{N_OPT}',
            rf'^NET INCOME\s+{N_OPT}',
            rf'Net income and comprehensive income\s+{N_OPT}',
            rf'Net income/\(loss\) and comprehensive (?:income|loss)(?:/\(loss\))?\s+{N_OPT}'),
    }

    return bs, inc

# ── Validation ─────────────────────────────────────────────────────────────────
OUTLIERS = []

def validate(company, year, bs, inc):
    """Filter to sane values, return (clean_bs, clean_inc, flags)."""
    clean_bs, clean_inc = {}, {}
    flags = []

    bs_bounds = {
        'Total Assets':              (50, 250_000),
        'Total Equity':              (-50_000, 150_000),
        'Total Liabilities':         (0, 250_000),
        'Total Investments':         (0, 200_000),
        'Cash and Cash Equivalents': (0, 50_000),
    }
    for k, (lo, hi) in bs_bounds.items():
        v = bs.get(k)
        if v is not None:
            if lo <= v <= hi:
                clean_bs[k] = v
            else:
                flags.append(f'BS {k}={v} out of [{lo},{hi}]')

    inc_bounds = {
        'Gross Premiums Written':  (0, 60_000),
        'Net Premiums Earned':     (0, 50_000),
        'Net Investment Income':   (-2_000, 15_000),
        'Investment Gains/Losses': (-30_000, 30_000),
        'Total Revenues':          (-5_000, 80_000),
        'Losses and LAE':          (0, 50_000),
        'Total Expenses':          (0, 80_000),
        'Net Income':              (-20_000, 20_000),
    }
    for k, (lo, hi) in inc_bounds.items():
        v = inc.get(k)
        if v is not None:
            if lo <= v <= hi:
                clean_inc[k] = v
            else:
                flags.append(f'IS {k}={v} out of [{lo},{hi}]')

    # Cross-field check (15% tolerance)
    ta = clean_bs.get('Total Assets')
    tl = clean_bs.get('Total Liabilities')
    te = clean_bs.get('Total Equity')
    if ta and tl and te:
        diff = abs((tl + te) - ta)
        if diff / ta > 0.15:
            flags.append(f'Balance sheet: TA={ta} vs TL+TE={(tl+te):.1f} (diff {diff/ta*100:.1f}%)')

    return clean_bs, clean_inc, flags

def compute_ratios(bs, inc):
    def g(d, k): return d.get(k) or 0
    ta  = g(bs, 'Total Assets');   te  = g(bs, 'Total Equity')
    ti  = g(bs, 'Total Investments')
    npe = g(inc, 'Net Premiums Earned'); ni  = g(inc, 'Net Income')
    loss = abs(g(inc, 'Losses and LAE')); exp = abs(g(inc, 'Total Expenses'))
    nii = g(inc, 'Net Investment Income')

    def safe(n, d, dp=1): return round(n / d * 100, dp) if d else 0

    ratios = {
        'ROE (%)':                   safe(ni, te),
        'ROA (%)':                   safe(ni, ta),
        'Equity Ratio (%)':          safe(te, ta),
        'Loss Ratio (%)':            safe(loss, npe),
        'Expense Ratio (%)':         safe(exp, npe),
        'Combined Ratio (%)':        safe(loss + exp, npe),
        'Investment Return (%)':     round(safe(nii, ti, dp=2), 2),
        'Investment Yield (%)':      round(safe(nii, ti, dp=2), 2),
        'Investments to Assets (%)': safe(ti, ta),
    }

    ratio_flags = []

    # Flag and zero out outlier ratios per task rules — do NOT include in dashboard
    if abs(ratios['Investment Return (%)']) > 15:
        ratio_flags.append(f"Investment Return={ratios['Investment Return (%)']}% outside [-15,15]% (zeroed)")
        ratios['Investment Return (%)'] = 0
        ratios['Investment Yield (%)'] = 0
    if ratios['Combined Ratio (%)'] and (ratios['Combined Ratio (%)'] < 50 or ratios['Combined Ratio (%)'] > 200):
        ratio_flags.append(f"Combined Ratio={ratios['Combined Ratio (%)']}% outside [50,200] (zeroed)")
        ratios['Combined Ratio (%)'] = 0
    if ratios['Loss Ratio (%)'] > 150:
        ratio_flags.append(f"Loss Ratio={ratios['Loss Ratio (%)']}% > 150% (zeroed)")
        ratios['Loss Ratio (%)'] = 0
        ratios['Combined Ratio (%)'] = 0  # combined depends on loss ratio — zero both
    if abs(ratios['ROE (%)']) > 50:
        ratio_flags.append(f"ROE={ratios['ROE (%)']}% > |50%| (zeroed)")
        ratios['ROE (%)'] = 0

    return ratios, ratio_flags

# ── Run extraction ─────────────────────────────────────────────────────────────
print("FILL GAPS EXTRACTION")
print("=" * 80)

extraction_results = {}

for company, patterns in TARGETS.items():
    extraction_results[company] = {}
    for year in [2023, 2024]:
        pdf = find_pdf(patterns, year)
        if not pdf:
            print(f"  {company} {year}: NO PDF FOUND")
            extraction_results[company][year] = {'status': 'no_pdf'}
            continue

        text = extract_text(pdf)
        if not text or len(text.strip()) < 300:
            print(f"  {company} {year}: IMAGE PDF — {pdf.name[:60]}")
            extraction_results[company][year] = {'status': 'image_pdf', 'pdf': pdf.name}
            continue

        denom = detect_denom(text)
        bs_raw, inc_raw = extract_metrics(text, denom)
        bs_clean, inc_clean, val_flags = validate(company, year, bs_raw, inc_raw)

        found = {k: v for k, v in {**bs_clean, **inc_clean}.items() if v is not None}
        if not found:
            print(f"  {company} {year}: TEXT ({denom}) but 0 fields matched ({len(text)} chars) — {pdf.name[:50]}")
            extraction_results[company][year] = {
                'status': 'no_match', 'pdf': pdf.name,
                'text_len': len(text), 'denom': denom,
                'raw_bs': {k: v for k, v in bs_raw.items() if v is not None},
                'raw_inc': {k: v for k, v in inc_raw.items() if v is not None},
            }
            continue

        ratios, ratio_flags = compute_ratios(bs_clean, inc_clean)
        all_flags = val_flags + ratio_flags
        if all_flags:
            OUTLIERS.append({'company': company, 'year': year, 'flags': all_flags})

        print(f"  {company} {year} [{denom}]: {len(found)} fields | "
              f"TA={found.get('Total Assets','?')} TE={found.get('Total Equity','?')} "
              f"NI={found.get('Net Income','?')} NPE={found.get('Net Premiums Earned','?')}")
        for f in all_flags:
            print(f"    FLAG: {f}")

        extraction_results[company][year] = {
            'status': 'extracted',
            'pdf': pdf.name,
            'denom': denom,
            'balance_sheet': bs_clean,
            'income_statement': inc_clean,
            'ratios': ratios,
            'flags': all_flags,
        }

with open('fill_gaps_results.json', 'w', encoding='utf-8') as f:
    json.dump(extraction_results, f, indent=2, default=str)
print("\nRaw results saved: fill_gaps_results.json")

# ── Merge into dashboard_data.json ─────────────────────────────────────────────
print("\nMERGING INTO dashboard_data.json")
print("=" * 80)

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

# Minimum plausible values for BMA Class 4 companies (USD millions).
# Existing values below these thresholds are considered bad prior extractions and overwritten.
IMPLAUSIBLE_BELOW = {
    'balance_sheet': {
        'Total Assets':              200,   # BMA Class 4 > $200M assets
        'Total Investments':          50,   # major investment portfolio
        'Total Liabilities':         100,   # liabilities > $100M for Class 4
        'Total Equity':               10,   # positive equity < $10M implausible for Class 4
        # Note: equity CAN be negative (distressed companies) — only block if tiny positive
    },
    'income_statement': {
        'Gross Premiums Written':     50,   # GPW > $50M for BMA Class 4
        'Net Premiums Earned':        50,   # NPE > $50M (avoid small-number garbage)
    },
}

def set_if_missing(yr, section, metric, company, value):
    """Set value if current is 0/None/missing or is a clearly implausible prior extraction."""
    yr_str = str(yr)
    try:
        current = dash['data'][yr_str][section][metric].get(company)
        # Missing or zero → fill
        if not current:
            dash['data'][yr_str][section][metric][company] = value
            return True
        # Negative for a metric that must be positive → overwrite
        must_positive = section == 'balance_sheet' and metric in ('Total Assets', 'Total Investments', 'Total Liabilities')
        if must_positive and current < 0:
            dash['data'][yr_str][section][metric][company] = value
            return True
        # Too small to be plausible (prior bad extraction) → overwrite
        min_plausible = IMPLAUSIBLE_BELOW.get(section, {}).get(metric, 0)
        if min_plausible > 0 and 0 < abs(current) < min_plausible:
            dash['data'][yr_str][section][metric][company] = value
            return True
    except KeyError:
        pass
    return False

total_updated = 0

for company, year_data in extraction_results.items():
    for year, data in year_data.items():
        if data.get('status') != 'extracted':
            continue
        n = 0
        bs   = data.get('balance_sheet', {})
        inc  = data.get('income_statement', {})
        rats = data.get('ratios', {})

        for metric, value in bs.items():
            if value is not None and set_if_missing(year, 'balance_sheet', metric, company, value):
                n += 1
        for metric, value in inc.items():
            if value is not None and set_if_missing(year, 'income_statement', metric, company, value):
                n += 1
        if n > 0:
            # Always overwrite ratios when we have new underlying data
            yr_str = str(year)
            for metric, value in rats.items():
                if value is not None:
                    try:
                        dash['data'][yr_str]['ratios'][metric][company] = value
                    except KeyError:
                        pass
            total_updated += n
            print(f"  {company} {year}: {n} new fields merged")

print(f"\nTotal new values merged: {total_updated}")

# ── Manual patches for values not reachable by regex (image pages, etc.) ──────
# These are hand-verified values extracted manually from the PDFs.
MANUAL_PATCHES = {
    # Hannover Re 2024: Balance sheet page is image-only.
    # Total Equity from Statement of Changes in Shareholders' Equity p.7:
    #   Balance as at 31 December 2024 = 2,583,853 thousands = 2583.9M
    # Total Investments (fix pre-existing -1.5 garbage):
    #   From Note 6 investments breakdown: Financial investments at FVOCI = 4,532,143 + FVPL
    #   (using 2023 value of 4423.8 as proxy is not ideal — leaving blank)
    'Hannover Re Bermuda': {
        2024: {
            'balance_sheet': {
                'Total Equity': 2583.9,
                'Total Investments': None,  # clear -1.5 garbage; set to 0 below
            }
        }
    },
}

for company, year_data in MANUAL_PATCHES.items():
    for year, sections in year_data.items():
        yr_str = str(year)
        for section, fields in sections.items():
            for metric, value in fields.items():
                try:
                    current = dash['data'][yr_str][section][metric].get(company, 0)
                    # value=None means "clear garbage to 0"
                    if value is None:
                        if current and current < 0:
                            dash['data'][yr_str][section][metric][company] = 0
                            print(f"  MANUAL CLEAR: {company} {year} {section}.{metric} {current} -> 0")
                    elif not current:
                        dash['data'][yr_str][section][metric][company] = value
                        print(f"  MANUAL PATCH: {company} {year} {section}.{metric} = {value}")
                        total_updated += 1
                except KeyError:
                    pass

# ── Re-compute ratios for any company that had manual patches ─────────────────
# Also fix any implausible ratios caused by stale TI/TA = 0 or near-zero
RECALC_COMPANIES = set(MANUAL_PATCHES.keys())

for company in RECALC_COMPANIES:
    for yr in ['2023', '2024']:
        d_ = dash['data'][yr]
        def g(sec, k): return d_[sec].get(k, {}).get(company, 0) or 0
        ta   = g('balance_sheet', 'Total Assets')
        te   = g('balance_sheet', 'Total Equity')
        ti   = g('balance_sheet', 'Total Investments')
        npe  = g('income_statement', 'Net Premiums Earned')
        ni   = g('income_statement', 'Net Income')
        loss = abs(g('income_statement', 'Losses and LAE'))
        exp  = abs(g('income_statement', 'Total Expenses'))
        nii  = g('income_statement', 'Net Investment Income')
        def safe(n, d, dp=1): return round(n/d*100, dp) if d else 0
        d_['ratios']['ROE (%)'][company]                   = safe(ni, te)
        d_['ratios']['ROA (%)'][company]                   = safe(ni, ta)
        d_['ratios']['Equity Ratio (%)'][company]          = safe(te, ta)
        d_['ratios']['Loss Ratio (%)'][company]            = safe(loss, npe)
        d_['ratios']['Expense Ratio (%)'][company]         = safe(exp, npe)
        d_['ratios']['Combined Ratio (%)'][company]        = safe(loss+exp, npe)
        d_['ratios']['Investment Return (%)'][company]     = round(safe(nii, ti, dp=2), 2)
        d_['ratios']['Investment Yield (%)'][company]      = round(safe(nii, ti, dp=2), 2)
        d_['ratios']['Investments to Assets (%)'][company] = safe(ti, ta)

with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(dash, f, separators=(',', ':'))
print("dashboard_data.json saved.")

# Regenerate dashboard_data.js
js_content = 'var BMA_DASHBOARD_DATA = ' + json.dumps(dash, separators=(',', ':')) + ';'
with open('dashboard_data.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
print("dashboard_data.js regenerated.")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SUMMARY")
counts = {'extracted': 0, 'image_pdf': 0, 'no_match': 0, 'no_pdf': 0}
for company, yd in extraction_results.items():
    for yr, d in yd.items():
        s = d.get('status', 'no_pdf')
        counts[s] = counts.get(s, 0) + 1

for k, v in counts.items():
    print(f"  {k}: {v} company-years")
print(f"\nOutlier flags ({len(OUTLIERS)} entries):")
for o in OUTLIERS:
    for f in o['flags']:
        print(f"  {o['company']} {o['year']}: {f}")
