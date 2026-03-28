"""Fast extraction using PyMuPDF (fitz) — much faster than pdfplumber."""
import fitz, re, json
from pathlib import Path

PDF_DIR = Path('pdfs')
N = r'([\d][\d,\.]*)'

TARGETS = {
    'Lancashire Insurance Company':                 ['Lancashire-Insurance-Company-Limited'],
    'XL Bermuda':                                   ['XL-Bermuda-Ltd'],
    'AXA XL Reinsurance':                           ['AXA-XL-Reinsurance', 'Axa-XL-Reinsurance'],
    'Endurance Specialty Insurance':                ['Endurance-Specialty-Insurance'],
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
    for pdf in sorted(PDF_DIR.glob('*.pdf')):
        if str(year) not in pdf.name: continue
        for pat in patterns:
            if pat.lower() in pdf.name.lower(): return pdf
    return None

def extract_text_fast(path, max_pages=35):
    doc = fitz.open(str(path))
    parts = []
    for i, page in enumerate(doc):
        if i >= max_pages: break
        parts.append(page.get_text())
    doc.close()
    return '\n'.join(parts)

def pn(s):
    if not s: return None
    s = s.strip().replace(',','').replace(' ','')
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    try:
        v = float(s)
        if neg: v = -v
        if abs(v) > 1_000_000: v = round(v/1_000_000,1)
        else: v = round(v,1)
        return v if v != 0 else None
    except: return None

def find(text, *pats):
    for pat in pats:
        m = re.search(pat, text, re.IGNORECASE|re.MULTILINE)
        if m:
            v = pn(m.group(1))
            if v: return v
    return None

def extract_metrics(text):
    N = r'([\d][\d,\.]*)'
    return {
        'bs': {
            'Total Assets':      find(text, rf'Total assets\s+{N}', rf'TOTAL ASSETS\s+{N}', rf'Total Assets\s+\$?\s*{N}'),
            'Total Equity':      find(text, rf"Total (?:shareholders'?|stockholders'?|members'?)\s*equity\s+{N}", rf'Total equity\s+{N}', rf'TOTAL EQUITY\s+{N}'),
            'Total Liabilities': find(text, rf'Total liabilities\s+(?!and){N}', rf'TOTAL LIABILITIES\s+(?!and){N}'),
            'Total Investments': find(text, rf'Total investments\s+{N}', rf'Investments\s+{N}'),
        },
        'is': {
            'Gross Premiums Written': find(text, rf'Gross premiums?\s*written\s+{N}', rf'GROSS PREMIUMS?\s*WRITTEN\s+{N}'),
            'Net Premiums Earned':    find(text, rf'Net premiums?\s*earned\s+{N}', rf'NET PREMIUMS?\s*EARNED\s+{N}'),
            'Net Investment Income':  find(text, rf'Net investment income\s+{N}', rf'NET INVESTMENT INCOME\s+{N}'),
            'Net Income':             find(text, rf'Net (?:income|profit|earnings?)\s+{N}', rf'Profit for the (?:year|period)\s+{N}', rf'NET INCOME\s+{N}'),
            'Losses and LAE':         find(text, rf'(?:Losses|Claims)[^\n]*incurred\s+{N}', rf'Net claims?\s+{N}'),
            'Total Expenses':         find(text, rf'Total (?:expenses?|costs? and expenses?)\s+{N}', rf'TOTAL EXPENSES?\s+{N}'),
        }
    }

results = {}
image_count = 0
extracted_count = 0

print("FAST EXTRACTION (PyMuPDF)\n" + "="*70)
for company, patterns in TARGETS.items():
    results[company] = {}
    for year in [2024, 2023]:
        pdf = find_pdf(patterns, year)
        if not pdf:
            results[company][year] = 'no_pdf'
            continue
        text = extract_text_fast(pdf)
        if not text.strip() or len(text) < 200:
            print(f"  {company} {year}: IMAGE PDF")
            results[company][year] = 'image'
            image_count += 1
            continue
        m = extract_metrics(text)
        found = {k:v for k,v in {**m['bs'], **m['is']}.items() if v}
        if not found:
            print(f"  {company} {year}: TEXT but no match ({len(text)} chars)")
            results[company][year] = 'no_match'
        else:
            extracted_count += 1
            print(f"  {company} {year}: {len(found)} fields | Assets={found.get('Total Assets','?')} Eq={found.get('Total Equity','?')} NPE={found.get('Net Premiums Earned','?')} NI={found.get('Net Income','?')}")
            results[company][year] = {'bs': m['bs'], 'is': m['is']}

with open('fast_extract_results.json','w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nDone. Extracted: {extracted_count}, Image PDFs: {image_count}")
print("Saved: fast_extract_results.json")
