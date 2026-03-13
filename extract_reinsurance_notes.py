"""
extract_reinsurance_notes.py — Extract reinsurance note data (assumed/ceded premiums
written + earned) from BMA financial statement PDFs.

Output: reinsurance_notes_extracted.json

Handles multiple table formats found across BMA filers:
  Format A: Row-per-label (Chubb): "Premiums written\nAssumed\n5,381,826\nCeded..."
  Format B: Direct+Assumed (Arch): "Premiums Written\nDirect\n...\nAssumed\n8,751..."
  Format C: Dotted lines (Somers): "Assumed  .........\n1,047,353"
  Format D: Written premiums heading (Everest): "Written premiums:\nAssumed\n4,912,842"
  Format E: Columnar (Partner Re): "Assumed $4,379,219 $4,335,900" (written, earned per row)
  Format F: SiriusPoint: Direct+Assumed+Gross+Ceded+Net
  Format G: Markel: column headers (Direct|Assumed|Ceded|Net), row labels (Written|Earned)
  Format H: IS-only (AXIS): Gross premiums written + Premiums ceded = net (no assumed split)
"""
import fitz, re, json
from pathlib import Path

PDF_DIR = Path('pdfs')
DATA_FILE = Path('dashboard_data.json')
OUT_FILE = Path('reinsurance_notes_extracted.json')

# ── Company → PDF filename patterns ───────────────────────────────────────────
COMPANY_PDF_PATTERNS = {
    'Arch Reinsurance':                             ['Arch-Reinsurance-Ltd'],
    'Ascot Bermuda':                                ['Ascot-Bermuda-Limited'],
    'Aspen Bermuda':                                ['Aspen-Bermuda-Limited'],
    'AXIS Specialty':                               ['AXIS-Specialty-Limited', 'Axis-Specialty-Limited',
                                                     'Axis-Specialty-Insurance-Limited'],
    'Chubb Tempest Reinsurance':                    ['Chubb-Tempest-Reinsurance-Ltd'],
    'Everest Reinsurance Bermuda':                  ['Everest-Reinsurance-Bermuda-Ltd'],
    'Hannover Re Bermuda':                          ['Hannover-Re-Bermuda-Ltd'],
    'Markel Bermuda':                               ['Markel-Bermuda-Limited'],
    'Partner Reinsurance Company':                  ['Partner-Reinsurance-Company-Ltd'],
    'Renaissance Reinsurance':                      ['Renaissance-Reinsurance-Ltd'],
    'Endurance Specialty Insurance':                ['Endurance-Specialty-Insurance-Ltd'],
    'XL Bermuda':                                   ['XL-Bermuda-Ltd'],
    'AXA XL Reinsurance':                           ['AXA-XL-Reinsurance-Ltd', 'Axa-XL-Reinsurance-Ltd'],
    'Validus Reinsurance':                          ['Validus-Reinsurance-Ltd'],
    'Somers Re':                                    ['Somers-Re-Ltd'],
    'Lancashire Insurance Company':                 ['Lancashire-Insurance-Company-Limited'],
    'Hiscox Insurance Company Bermuda':             ['Hiscox-Insurance-Company-Bermuda-Limited'],
    'Canopius Reinsurance':                         ['Canopius-Reinsurance-Limited'],
    'Conduit Reinsurance':                          ['Conduit-Reinsurance-Limited'],
    'Fidelis Insurance Bermuda':                    ['Fidelis-Insurance-Bermuda-Limited'],
    'Fortitude Reinsurance Company':                ['Fortitude-Reinsurance-Company-Ltd'],
    'Group Ark Insurance':                          ['Group-Ark-Insurance-Limited'],
    'Hamilton Re':                                  ['Hamilton-Re-Ltd'],
    'Harrington Re':                                ['Harrington-Re-Ltd'],
    'Liberty Specialty Markets Bermuda':            ['Liberty-Specialty-Markets-Bermuda-Limited'],
    'MS Amlin AG':                                  ['MS-Amlin-AG'],
    'Premia Reinsurance':                           ['Premia-Reinsurance-Ltd'],
    'Starr Insurance & Reinsurance':                ['Starr-Insurance--Reinsurance-Limited',
                                                     'Starr-Insurance-'],
    'Vantage Risk':                                 ['Vantage-Risk-Ltd'],
    'SiriusPoint Bermuda Insurance':                ['SiriusPoint-Bermuda-Insurance-Company-Ltd',
                                                     'Siriuspoint-Bermuda-Insurance-Company-Ltd'],
    'ABR Reinsurance Ltd.':                         ['ABR-Reinsurance-Ltd'],
    'Allied World Assurance Company Ltd':           ['Allied-World-Assurance-Company-Ltd'],
    'American International Reinsurance Company Ltd.': ['American-International-Reinsurance-Company-Ltd'],
    'Antares Reinsurance Company Limited':          ['Antares-Reinsurance-Company-Limited'],
    'Argo Re Ltd.':                                 ['Argo-Re-Ltd'],
    'Brit Reinsurance Bermuda Limited':             ['Brit-Reinsurance-Bermuda-Limited'],
    'Convex Re Limited':                            ['Convex-Re-Limited'],
    'DaVinci Reinsurance Ltd.':                     ['DaVinci-Reinsurance-Ltd', 'Davinci-Reinsurance-Ltd'],
    'Everest International Reinsurance Ltd.':       ['Everest-International-Reinsurance-Ltd'],
    'Fortitude International Reinsurance Ltd.':     ['Fortitude-International-Reinsurance-Ltd'],
}

YEAR_VALS = set(range(2010, 2030))


# ── PDF finder ─────────────────────────────────────────────────────────────────
def find_pdf(patterns, year):
    year_str = str(year)
    candidates = []
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        name = pdf.name
        if (f'---{year_str}-Financial-Statement' in name or
                f'----{year_str}-Financial-Statement' in name or
                f'--{year_str}-Financial-Statement' in name or
                f'-{year_str}-Financial-Statement' in name):
            for pat in patterns:
                if pat.lower() in name.lower():
                    candidates.append(pdf)
                    break
    if candidates:
        return candidates[-1]
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        name = pdf.name
        if year_str in name:
            for pat in patterns:
                if pat.lower() in name.lower():
                    return pdf
    return None


# ── Text extraction ────────────────────────────────────────────────────────────
def extract_text(path, max_pages=70):
    try:
        doc = fitz.open(str(path))
        parts = [page.get_text() for i, page in enumerate(doc) if i < max_pages]
        doc.close()
        return '\n'.join(parts)
    except Exception:
        return ''


# ── Denomination detection ─────────────────────────────────────────────────────
def detect_denom(text):
    sample = text[:15000].lower()
    if re.search(r'expressed\s+in\s+(?:thousands|000s)\b|in\s+thousands\s+of|'
                 r'\(in\s+thousands\)|in\s+thousands\b', sample):
        return 'thousands'
    if re.search(r'expressed\s+in\s+(?:millions)\b|in\s+millions\s+of|'
                 r'\(in\s+millions\)|in\s+millions\b', sample):
        return 'millions'
    big = re.findall(r'[\d,]{9,}', sample)
    if big:
        return 'thousands'
    return 'thousands'


# ── Number parsing ─────────────────────────────────────────────────────────────
def pn(s, denom='thousands'):
    if not s:
        return None
    s = str(s).strip().replace(',', '').replace(' ', '').replace('\n', '')
    neg = (s.startswith('(') and s.endswith(')')) or s.startswith('-')
    s = s.strip('()').lstrip('-')
    try:
        v = float(s)
        if int(abs(v)) in YEAR_VALS:
            return None
        if neg:
            v = -v
        if denom == 'thousands':
            if abs(v) > 1_000_000_000:
                v = round(v / 1_000_000, 1)
            elif abs(v) > 1_000:
                v = round(v / 1_000, 1)
            else:
                v = round(v, 1)
        elif denom == 'millions':
            v = round(v, 1)
        else:
            if abs(v) > 1_000_000:
                v = round(v / 1_000, 1)
            else:
                v = round(v, 1)
        return v if v != 0 else None
    except Exception:
        return None


# ── Number patterns ─────────────────────────────────────────────────────────────
N3 = r'(\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\d{5,}(?:\.\d+)?)'


def extract_first_num(s, denom):
    """Extract the first valid number from string s."""
    # First: comma-separated groups (e.g. 1,748.7 or 5,381,826)
    m = re.search(r'(\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?)', s)
    if m:
        v = pn(m.group(1), denom)
        if v is not None:
            return v
    # Second: 5+ digit plain number (e.g. 48012)
    m = re.search(r'(\(?\d{5,}(?:\.\d+)?\)?)', s)
    if m:
        v = pn(m.group(1), denom)
        if v is not None:
            return v
    # Third: decimal number without commas (e.g. 989.5, (74.9)) — common in millions-denom docs
    # Uses decimal to distinguish from year integers like 2023
    m = re.search(r'(\(?\d{1,4}\.\d+\)?)', s)
    if m:
        v = pn(m.group(1), denom)
        if v is not None:
            return v
    return None


def find_val(text, denom, *pats):
    for pat in pats:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            grp = m.group(m.lastindex) if m.lastindex else m.group(1)
            grp = re.sub(r'^\$\s*', '', grp.strip())
            v = pn(grp, denom)
            if v is not None:
                return v
    return None


# ── Find next numeric value after a label line ────────────────────────────────
def parse_next_line_value(lines, label_idx, denom, look_ahead=8):
    """Scan next lines after label to find first numeric value."""
    for j in range(1, look_ahead + 1):
        if label_idx + j >= len(lines):
            break
        candidate = lines[label_idx + j].strip()
        if not candidate:
            continue
        # Skip standalone $ signs, em-dashes, year numbers
        if re.match(r'^\$\s*$', candidate):
            continue
        if re.match(r'^—+$', candidate) or re.match(r'^[-–—]+$', candidate):
            continue
        if re.match(r'^20\d{2}$', candidate):
            continue
        # Try to extract number (take first match from line)
        v = extract_first_num(candidate, denom)
        if v is not None:
            return v
    return None


# ── Find the reinsurance data-table section ────────────────────────────────────
# Heading variants that indicate a premiums written table
PW_HEADINGS = [
    r'^premiums?\s+written\s*:?\s*$',
    r'^written\s+premiums?\s*:?\s*$',
    r'^premiums\s+written\s+and\s+earned\s*:?\s*$',
]

def is_pw_heading(sl):
    """Return True if sl is a premiums-written heading."""
    for pat in PW_HEADINGS:
        if re.match(pat, sl):
            return True
    return False

def is_pe_heading(sl):
    """Return True if sl is a premiums-earned heading."""
    return bool(re.match(r'^premiums?\s+earned\s*:?\s*$', sl))


def find_reinsurance_section(full_text):
    """
    Find the slice of text containing the reinsurance DATA table.
    Returns (section_text, start_line_idx, strategy_idx) or ('', -1, -1)
    """
    lines = full_text.split('\n')

    def has_reins_data(window_lines):
        """Check if window contains assumed/ceded/numbers."""
        t = '\n'.join(window_lines)
        return (re.search(r'\bAssumed\b', t, re.IGNORECASE) and
                re.search(r'\bCeded\b', t, re.IGNORECASE) and
                re.search(r'\d{1,3}(?:,\d{3})+', t))

    # Strategy 1: Find "Premiums written" heading (any variant) followed by Assumed+Ceded+numbers
    for i, line in enumerate(lines):
        sl = line.strip().lower()
        if is_pw_heading(sl):
            window = lines[i:i+80]
            if has_reins_data(window):
                return '\n'.join(lines[max(0, i-2):i+120]), i, 1

    # Strategy 2: Find "Premiums" then "Written" on NEXT line (columnar format e.g. Partner Re)
    for i in range(len(lines) - 1):
        sl_cur = lines[i].strip().lower()
        sl_next = lines[i+1].strip().lower()
        if sl_cur == 'premiums' and sl_next in ('written', 'written:'):
            window = lines[i:i+80]
            if has_reins_data(window):
                return '\n'.join(lines[max(0, i-2):i+120]), i, 2

    # Strategy 3: "Reinsurance" note heading followed by Premiums-written + data within 120 lines
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (re.match(r'^(?:\d+\.?\s*)?[Rr]einsurance\s*$', stripped) or
                re.match(r'^(?:\d+\.?\s*)?[Rr]einsurance\b[^:\n]{0,60}$', stripped)):
            window = lines[i:i+130]
            window_text = '\n'.join(window)
            has_pw = (re.search(r'Premiums?\s+[Ww]ritten', window_text) or
                      re.search(r'Written\s+[Pp]remiums?', window_text))
            if has_pw and has_reins_data(window):
                return '\n'.join(lines[i:i+150]), i, 3

    # Strategy 4: "Effects of reinsurance on premiums" heading
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.search(r'[Ee]ffects?\s+of\s+reinsurance\s+on\s+premiums?', stripped):
            window = lines[i:i+80]
            if has_reins_data(window):
                return '\n'.join(lines[i:i+100]), i, 4

    # Strategy 5: Bare "Assumed" line with context containing premiums data + numbers
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^Assumed\s*$', stripped, re.IGNORECASE):
            context_start = max(0, i - 15)
            context = '\n'.join(lines[context_start:i+60])
            has_pw = (re.search(r'Premiums?\s+[Ww]ritten', context, re.IGNORECASE) or
                      re.search(r'Written\s+[Pp]remiums?', context, re.IGNORECASE))
            has_ceded = re.search(r'\bCeded\b', context, re.IGNORECASE)
            has_num = re.search(r'\d{1,3}(?:,\d{3})+', context)
            if has_pw and has_ceded and has_num:
                return '\n'.join(lines[max(0, i-20):i+100]), i, 5

    # Strategy 6: Inline "Assumed premiums written" patterns
    m = re.search(rf'[Aa]ssumed\s+premiums?\s+written\s+{N3}', full_text)
    if m:
        start_pos = max(0, m.start() - 300)
        end_pos = min(len(full_text), m.end() + 600)
        line_idx = full_text[:start_pos].count('\n')
        return full_text[start_pos:end_pos], line_idx, 6

    return '', -1, -1


# ── Extract from block-based section ──────────────────────────────────────────
def is_label_line(sl, label):
    """True if line is exactly the label (possibly with trailing dots/dashes/spaces)."""
    return bool(re.match(rf'^{label}[\s\.\-–_\u2026]*$', sl, re.IGNORECASE))


def extract_reinsurance_note(section_text, denom):
    result = {}
    lines = section_text.split('\n')

    # ── Phase 1: Block-state extraction ─────────────────────────────────────
    block_state = None
    block_lines = {'written': [], 'earned': [], 'losses': []}
    prev_sl = ''

    for line in lines:
        stripped = line.strip()
        sl = stripped.lower()

        # Detect block transitions
        new_state = None
        if is_pw_heading(sl):
            new_state = 'written'
        elif sl == 'written' and prev_sl == 'premiums':
            new_state = 'written'
        # "Net premiums written" as a section header (Liberty Specialty format)
        elif sl == 'net premiums written' and block_state is None:
            new_state = 'written'
        elif is_pe_heading(sl):
            new_state = 'earned'
        elif sl == 'earned' and prev_sl == 'premiums':
            new_state = 'earned'
        # "Net premiums earned" as a section header
        elif sl == 'net premiums earned' and block_state == 'written':
            new_state = 'earned'
        elif re.match(r'^(?:incurred\s+)?losses?\s+(?:and\s+)?(?:lae|loss\s+adjustment|claim)', sl):
            new_state = 'losses'
        elif sl == 'expenses' and re.search(r'losses?', prev_sl):
            new_state = 'losses'

        if new_state:
            block_state = new_state
        elif block_state == 'written' and is_pe_heading(sl):
            block_state = 'earned'

        if block_state:
            block_lines[block_state].append(line)

        prev_sl = sl

    def extract_block(block_name):
        blines = block_lines[block_name]
        if not blines:
            return {}
        vals = {}
        for idx, line in enumerate(blines):
            stripped = line.strip()
            sl = stripped.lower()

            if is_label_line(sl, 'assumed') and 'assumed' not in vals:
                v = parse_next_line_value(blines, idx, denom)
                if v is not None:
                    vals['assumed'] = v
            elif is_label_line(sl, 'ceded') and 'ceded' not in vals:
                v = parse_next_line_value(blines, idx, denom)
                if v is not None:
                    vals['ceded'] = v
            elif is_label_line(sl, 'net') and 'net' not in vals:
                v = parse_next_line_value(blines, idx, denom)
                if v is not None:
                    vals['net'] = v
            # Inline: "Assumed   8,751" or "Assumed   8,751   6,785"
            elif re.match(r'^assumed\b', sl) and not is_label_line(sl, 'assumed') and 'assumed' not in vals:
                v = extract_first_num(stripped[len('Assumed'):].strip(), denom)
                if v is not None:
                    vals['assumed'] = v
            elif re.match(r'^ceded\b', sl) and not is_label_line(sl, 'ceded') and 'ceded' not in vals:
                v = extract_first_num(stripped[len('Ceded'):].strip(), denom)
                if v is not None:
                    vals['ceded'] = v
            elif re.match(r'^net\s+(?:premiums?|written|earned)\b', sl) and 'net' not in vals:
                v = extract_first_num(stripped, denom)
                if v is not None:
                    vals['net'] = v
        return vals

    written = extract_block('written')
    earned = extract_block('earned')
    losses = extract_block('losses')

    if written.get('assumed'):
        result['assumed_premiums_written'] = written['assumed']
    if written.get('ceded'):
        result['ceded_premiums_written'] = -abs(written['ceded'])
    if written.get('net'):
        result['net_premiums_written'] = written['net']
    if earned.get('assumed'):
        result['assumed_premiums_earned'] = earned['assumed']
    if earned.get('ceded'):
        result['ceded_premiums_earned'] = -abs(earned['ceded'])
    if earned.get('net'):
        result['net_premiums_earned'] = earned['net']
    if losses.get('assumed'):
        result['assumed_losses_paid'] = losses['assumed']
    if losses.get('ceded'):
        result['ceded_losses_recovered'] = -abs(losses['ceded'])
    if losses.get('net'):
        result['net_losses_incurred'] = losses['net']

    # ── Phase 2: Columnar extraction (Partner Re / Markel format) ────────────
    # If Phase 1 missing key fields, try columnar: Assumed/Ceded/Net rows × columns
    if not result.get('assumed_premiums_written'):
        col_result = try_extract_columnar(section_text, denom)
        for k, v in col_result.items():
            if v is not None and k not in result:
                result[k] = v

    # ── Phase 3: Fallback regexes across full section ─────────────────────────
    def fallback(key, *pats):
        if not result.get(key):
            v = find_val(section_text, denom, *pats)
            if v is not None:
                result[key] = v

    fallback('assumed_premiums_written',
        rf'[Aa]ssumed\s+premiums?\s+written\s+{N3}',
        rf'[Gg]ross\s+premiums?\s+written\b[^\n]*{N3}',
    )
    fallback('ceded_premiums_written',
        rf'[Cc]eded\s+premiums?\s+written\s+{N3}',
    )
    fallback('net_premiums_written',
        rf'[Nn]et\s+premiums?\s+written\s+{N3}',
    )
    fallback('assumed_premiums_earned',
        rf'[Aa]ssumed\s+premiums?\s+earned\s+{N3}',
    )
    fallback('ceded_premiums_earned',
        rf'[Cc]eded\s+premiums?\s+earned\s+{N3}',
    )
    fallback('net_premiums_earned',
        rf'[Nn]et\s+premiums?\s+earned\s+{N3}',
    )

    # Fix signs
    for k in ('ceded_premiums_written', 'ceded_premiums_earned', 'ceded_losses_recovered'):
        if result.get(k) and result[k] > 0:
            result[k] = -result[k]

    return {k: v for k, v in result.items() if v is not None}


def try_extract_columnar(section_text, denom):
    """
    Handle columnar format where Assumed/Ceded/Net are rows and
    Premiums Written / Premiums Earned / Losses are columns.
    Each Assumed/Ceded/Net row has multiple values: [written, earned, losses].
    """
    lines = section_text.split('\n')
    label_values = {}  # 'assumed' → [val1, val2, ...]
    current_label = None
    current_vals = []

    for line in lines:
        stripped = line.strip()
        sl = stripped.lower()

        if is_label_line(sl, 'assumed'):
            if current_label:
                label_values[current_label] = current_vals
            current_label = 'assumed'
            current_vals = []
        elif is_label_line(sl, 'ceded'):
            if current_label:
                label_values[current_label] = current_vals
            current_label = 'ceded'
            current_vals = []
        elif is_label_line(sl, 'net') or re.match(r'^net\s+(?:premiums?|written|earned)\b', sl):
            if current_label:
                label_values[current_label] = current_vals
            current_label = 'net'
            current_vals = []
        elif current_label is not None:
            # Accumulate numbers
            for m in re.finditer(r'(\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?)', stripped):
                v = pn(m.group(1), denom)
                if v is not None:
                    current_vals.append(v)
            # If no comma numbers, try plain multi-digit
            if not current_vals or (stripped and not re.search(r'\d', stripped)):
                pass
        # Stop collecting on section boundaries
        if re.match(r'^(?:losses?\s+and\s+loss|incurred|bellemeade|affiliated)', sl):
            if current_label:
                label_values[current_label] = current_vals
            current_label = None
            current_vals = []

    if current_label:
        label_values[current_label] = current_vals

    result = {}
    assumed = label_values.get('assumed', [])
    ceded = label_values.get('ceded', [])
    net = label_values.get('net', [])

    if len(assumed) >= 1:
        result['assumed_premiums_written'] = assumed[0]
    if len(assumed) >= 2:
        result['assumed_premiums_earned'] = assumed[1]
    if len(ceded) >= 1:
        result['ceded_premiums_written'] = -abs(ceded[0])
    if len(ceded) >= 2:
        result['ceded_premiums_earned'] = -abs(ceded[1])
    if len(net) >= 1:
        result['net_premiums_written'] = net[0]
    if len(net) >= 2:
        result['net_premiums_earned'] = net[1]

    return result


# ── Determine extraction status ────────────────────────────────────────────────
def extraction_status(result):
    core = ['assumed_premiums_written', 'ceded_premiums_written', 'net_premiums_written',
            'assumed_premiums_earned', 'ceded_premiums_earned', 'net_premiums_earned']
    found = sum(1 for k in core if result.get(k) is not None)
    if found >= 4:
        return 'success'
    elif found >= 2:
        return 'partial'
    else:
        return 'not_found'


# ── Cross-check against existing GPW ──────────────────────────────────────────
def cross_check(company, year, result, dashboard_data):
    existing_gpw = (dashboard_data.get('data', {})
                    .get(str(year), {})
                    .get('income_statement', {})
                    .get('Gross Premiums Written', {})
                    .get(company))
    assumed = result.get('assumed_premiums_written')
    if not assumed or not existing_gpw or existing_gpw == 0:
        return 'no_prior_data', None
    delta_pct = abs(assumed - existing_gpw) / max(abs(existing_gpw), 0.001) * 100
    if delta_pct <= 5.0:
        return 'match', round(delta_pct, 2)
    else:
        return 'mismatch', round(delta_pct, 2)


def get_snippet(section_text, max_lines=15):
    lines = [l for l in section_text.split('\n') if l.strip()][:max_lines]
    return '\n'.join(lines)


# ── Main extraction loop ───────────────────────────────────────────────────────
def main():
    dashboard_data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    companies = dashboard_data['companies']

    results = {}
    stats = {'total': 0, 'success': 0, 'partial': 0, 'not_found': 0,
             'image_only': 0, 'no_pdf': 0}

    print(f"{'Company':<50} {'Year'} {'Status':<12} {'APW':>10} {'CPW':>10} {'NPW':>10} {'Xchk'}")
    print("-" * 115)

    for company in companies:
        patterns = COMPANY_PDF_PATTERNS.get(company)
        if not patterns:
            print(f"  !! No PDF pattern for: {company}")
            results[company] = {}
            continue

        results[company] = {}

        for year in [2023, 2024]:
            stats['total'] += 1
            pdf = find_pdf(patterns, year)

            if not pdf:
                results[company][str(year)] = {
                    'extraction_status': 'no_pdf', 'source_pdf': None}
                stats['no_pdf'] += 1
                print(f"  {company:<50} {year} {'no_pdf'}")
                continue

            text = extract_text(pdf)

            if not text.strip() or len(text) < 300:
                results[company][str(year)] = {
                    'extraction_status': 'image_only', 'source_pdf': pdf.name}
                stats['image_only'] += 1
                print(f"  {company:<50} {year} {'image_only'}")
                continue

            denom = detect_denom(text)
            section_text, section_line, strat_i = find_reinsurance_section(text)

            if not section_text:
                results[company][str(year)] = {
                    'extraction_status': 'not_found', 'source_pdf': pdf.name, 'denom': denom}
                stats['not_found'] += 1
                print(f"  {company:<50} {year} {'not_found'}")
                continue

            extracted = extract_reinsurance_note(section_text, denom)
            status = extraction_status(extracted)

            xchk_result, xchk_delta = cross_check(company, year, extracted, dashboard_data)

            entry = {
                **extracted,
                'cross_check_gpw_match': (xchk_result == 'match'),
                'cross_check_delta_pct': xchk_delta,
                'cross_check_result': xchk_result,
                'extraction_status': status,
                'source_pdf': pdf.name,
                'denom': denom,
                'strategy': strat_i,
                'raw_text_snippet': get_snippet(section_text),
            }
            results[company][str(year)] = entry

            stats[status] += 1

            apw = extracted.get('assumed_premiums_written')
            cpw = extracted.get('ceded_premiums_written')
            npw = extracted.get('net_premiums_written')
            xchk = (f"{xchk_result}({xchk_delta:.1f}%)"
                    if xchk_delta is not None else xchk_result)

            fmt = lambda v: f"{v:>10.1f}" if isinstance(v, (int, float)) else f"{'—':>10}"
            print(f"  {company:<50} {year} {status:<12} {fmt(apw)} {fmt(cpw)} {fmt(npw)} {xchk}")

    print(f"\nStats: {stats}")
    OUT_FILE.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f"Wrote {OUT_FILE}")
    return results, stats, dashboard_data


if __name__ == '__main__':
    main()
