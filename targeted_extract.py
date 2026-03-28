"""
Targeted pdfplumber extractor for the 19 data-pending companies.
Extracts key financial metrics using regex on raw text.
"""
import pdfplumber, re, json, os
from pathlib import Path

PDF_DIR = Path('pdfs')

# 19 companies: dashboard_name -> partial PDF name patterns for 2023 + 2024
TARGETS = {
    'Lancashire Insurance Company':                 ['Lancashire-Insurance-Company-Limited'],
    'XL Bermuda':                                   ['XL-Bermuda-Ltd'],
    'AXA XL Reinsurance':                           ['AXA-XL-Reinsurance-Ltd', 'Axa-XL-Reinsurance-Ltd'],
    'Endurance Specialty Insurance':                ['Endurance-Specialty-Insurance-Ltd'],
    'Validus Reinsurance':                          ['Validus-Reinsurance-Ltd.'],
    'Somers Re':                                    ['Somers-Re-Ltd'],
    'Canopius Reinsurance':                         ['Canopius-Reinsurance-Limited'],
    'Fidelis Insurance Bermuda':                    ['Fidelis-Insurance-Bermuda-Limited'],
    'Argo Re Ltd.':                                 ['Argo-Re-Ltd.'],
    'Hiscox Insurance Company Bermuda':             ['Hiscox-Insurance-Company-Bermuda-Limited'],
    'Starr Insurance & Reinsurance':                ['Starr-Insurance'],
    'Fortitude Reinsurance Company':                ['Fortitude-Reinsurance-Company-Ltd'],
    'SiriusPoint Bermuda Insurance':                ['SiriusPoint-Bermuda', 'Siriuspoint-Bermuda'],
    'Conduit Reinsurance':                          ['Conduit-Reinsurance-Limited'],
    'Liberty Specialty Markets Bermuda':            ['Liberty-Specialty-Markets-Bermuda-Limited'],
    'Hamilton Re':                                  ['Hamilton-Re-Ltd'],
    'American International Reinsurance Company Ltd.': ['American-International-Reinsurance-Company-Ltd'],
    'Brit Reinsurance Bermuda Limited':             ['Brit-Reinsurance-Bermuda-Limited'],
    'Fortitude International Reinsurance Ltd.':     ['Fortitude-International-Reinsurance-Ltd'],
}

def find_pdf(patterns, year):
    year_str = str(year)
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        name = pdf.name
        if year_str not in name:
            continue
        for pat in patterns:
            if pat.lower() in name.lower():
                return pdf
    return None

def extract_text(pdf_path, max_pages=40):
    """Extract full text from a PDF using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception as e:
        return None, str(e)
    full = '\n'.join(text_parts)
    return full if full.strip() else None, None

def parse_num(s):
    """Parse a number string to float in millions."""
    if not s:
        return None
    s = s.strip().replace(',', '').replace(' ', '')
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    try:
        v = float(s)
        if neg:
            v = -v
        # Convert from raw to millions if > 1M
        if abs(v) > 1_000_000:
            v = round(v / 1_000_000, 1)
        else:
            v = round(v, 1)
        return v if v != 0 else None
    except:
        return None

def search_metric(text, *patterns):
    """Try each regex pattern, return first match as float in millions."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            v = parse_num(m.group(1))
            if v:
                return v
    return None

def extract_financials(text):
    """Extract key metrics from financial statement text."""
    # Numbers: may be integers with commas, or decimals, optionally in parens
    N = r'([\(\d][\d,\.\s\)]*)'

    return {
        'balance_sheet': {
            'Total Assets':      search_metric(text,
                rf'Total assets\s+{N}',
                rf'TOTAL ASSETS\s+{N}',
                rf'Total Assets\s+\$?\s*{N}'),
            'Total Equity':      search_metric(text,
                rf"Total (shareholders'?|stockholders'?|members'?) equity\s+{N}",
                rf'Total equity\s+{N}',
                rf'TOTAL EQUITY\s+{N}',
                rf"Shareholders'? equity\s+{N}"),
            'Total Liabilities': search_metric(text,
                rf'Total liabilities\s+{N}',
                rf'TOTAL LIABILITIES\s+{N}'),
            'Total Investments': search_metric(text,
                rf'Total investments\s+{N}',
                rf'TOTAL INVESTMENTS\s+{N}',
                rf'Investments\s+{N}'),
        },
        'income_statement': {
            'Gross Premiums Written':  search_metric(text,
                rf'Gross premiums? written\s+{N}',
                rf'GROSS PREMIUMS? WRITTEN\s+{N}'),
            'Net Premiums Earned':     search_metric(text,
                rf'Net premiums? earned\s+{N}',
                rf'NET PREMIUMS? EARNED\s+{N}'),
            'Net Investment Income':   search_metric(text,
                rf'Net investment income\s+{N}',
                rf'NET INVESTMENT INCOME\s+{N}'),
            'Net Income':              search_metric(text,
                rf'Net (income|profit|earnings?)\s+(?:for the (year|period)\s+)?{N}',
                rf'NET (INCOME|PROFIT|EARNINGS?)\s+{N}',
                rf'Profit for the (year|period)\s+{N}',
                rf'Net income \(loss\)\s+{N}'),
            'Total Revenues':          search_metric(text,
                rf'Total revenues?\s+{N}',
                rf'Total income\s+{N}',
                rf'TOTAL REVENUES?\s+{N}'),
            'Total Expenses':          search_metric(text,
                rf'Total (expenses?|costs? and expenses?)\s+{N}',
                rf'TOTAL EXPENSES?\s+{N}'),
            'Losses and LAE':          search_metric(text,
                rf'(Losses|Claims) (and|incurred|paid|LAE|loss adjustment)\s+{N}',
                rf'Net claims? (and claim expenses?|incurred)\s+{N}'),
        }
    }

def recalc_ratios(bs, inc):
    def g(d, k): return d.get(k) or 0
    ta   = g(bs, 'Total Assets')
    te   = g(bs, 'Total Equity')
    ti   = g(bs, 'Total Investments')
    npe  = g(inc, 'Net Premiums Earned')
    ni   = g(inc, 'Net Income')
    loss = abs(g(inc, 'Losses and LAE'))
    exp  = abs(g(inc, 'Total Expenses'))
    nii  = g(inc, 'Net Investment Income')
    def safe(n, d, dp=1): return round(n/d*100, dp) if d else 0
    return {
        'ROE (%)':                   safe(ni, te),
        'ROA (%)':                   safe(ni, ta),
        'Equity Ratio (%)':          safe(te, ta),
        'Loss Ratio (%)':            safe(loss, npe),
        'Expense Ratio (%)':         safe(exp, npe),
        'Combined Ratio (%)':        safe(loss+exp, npe),
        'Investment Return (%)':     round(safe(nii, ti, dp=2), 2),
        'Investment Yield (%)':      round(safe(nii, ti, dp=2), 2),
        'Investments to Assets (%)': safe(ti, ta),
    }

# ── Run extraction ─────────────────────────────────────────────────────────
results = {}
print("TARGETED PDF EXTRACTION")
print("=" * 80)

for company, patterns in TARGETS.items():
    results[company] = {}
    for year in [2023, 2024]:
        pdf_path = find_pdf(patterns, year)
        if not pdf_path:
            print(f"  {company} {year}: NO PDF FOUND")
            results[company][year] = {'status': 'no_pdf', 'fields': {}}
            continue

        text, err = extract_text(pdf_path)
        if not text:
            print(f"  {company} {year}: IMAGE-BASED (no text) — {pdf_path.name[:60]}")
            results[company][year] = {'status': 'image_pdf', 'fields': {}}
            continue

        financials = extract_financials(text)
        # Count non-None fields
        all_fields = {**financials['balance_sheet'], **financials['income_statement']}
        found = {k: v for k, v in all_fields.items() if v is not None}

        if not found:
            print(f"  {company} {year}: TEXT PDF but 0 fields matched — {pdf_path.name[:60]}")
            results[company][year] = {'status': 'no_match', 'fields': {}}
        else:
            ratios = recalc_ratios(financials['balance_sheet'], financials['income_statement'])
            print(f"  {company} {year}: {len(found)} fields  Assets={found.get('Total Assets','?')}  Eq={found.get('Total Equity','?')}  NPE={found.get('Net Premiums Earned','?')}  NI={found.get('Net Income','?')}")
            results[company][year] = {
                'status': 'extracted',
                'fields': financials,
                'ratios': ratios,
                'pdf': pdf_path.name
            }

# ── Save results ───────────────────────────────────────────────────────────
with open('targeted_extraction_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to targeted_extraction_results.json")

# ── Summary ────────────────────────────────────────────────────────────────
print("\nSUMMARY:")
can_update = [(c, y) for c, ydata in results.items() for y, d in ydata.items() if d['status'] == 'extracted']
image_pdfs = [(c, y) for c, ydata in results.items() for y, d in ydata.items() if d['status'] == 'image_pdf']
no_match   = [(c, y) for c, ydata in results.items() for y, d in ydata.items() if d['status'] == 'no_match']
print(f"  Extractable:  {len(can_update)} company-years")
print(f"  Image-based:  {len(image_pdfs)} company-years (need OCR)")
print(f"  Text but no match: {len(no_match)} company-years")
