"""
Compare claude-data extracted_financials.json vs current dashboard_data.json
"""
import json, re
from collections import defaultdict

DUMMY_COMPANIES = [
    'XL Bermuda', 'AXA XL Reinsurance', 'Endurance Specialty Insurance',
    'Validus Reinsurance', 'Hiscox Insurance Company Bermuda',
    'Starr Insurance & Reinsurance', 'Fortitude Reinsurance Company',
    'SiriusPoint Bermuda Insurance', 'Somers Re', 'MS Amlin AG',
    'Lancashire Insurance Company', 'Conduit Reinsurance',
    'Liberty Specialty Markets Bermuda', 'Canopius Reinsurance',
    'Hamilton Re', 'Fidelis Insurance Bermuda',
]
ZERO_COMPANIES = [
    'American International Reinsurance Company Ltd.',
    'Argo Re Ltd.',
    'Brit Reinsurance Bermuda Limited',
    'Fortitude International Reinsurance Ltd.'
]
ALL_TARGETS = DUMMY_COMPANIES + ZERO_COMPANIES

with open(r'C:\Users\nthig\.openclaw\workspace\claude-data\bma-filings\data\extracted_financials.json', encoding='utf-8', errors='replace') as f:
    extracted = json.load(f)

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

# Build a lookup: company_name_lower -> {year -> data}
ext_by_company = defaultdict(dict)
for key, val in extracted.items():
    # key format: "Company Name - 2024"
    m = re.match(r'^(.+?)\s*-\s*(\d{4})$', key)
    if m:
        company_raw = m.group(1).strip()
        year = int(m.group(2))
        ext_by_company[company_raw.lower()][year] = val

# Helper: fuzzy match company name
def find_in_extracted(target_name):
    t = target_name.lower().strip()
    # Exact match
    if t in ext_by_company:
        return ext_by_company[t]
    # Partial: target contains key or key contains target
    for key in ext_by_company:
        # Try key words overlap
        t_words = set(re.findall(r'\w+', t))
        k_words = set(re.findall(r'\w+', key))
        overlap = t_words & k_words - {'reinsurance','insurance','bermuda','ltd','limited','company','re'}
        if len(overlap) >= 2:
            return ext_by_company[key]
    return None

# Key financial fields to check
BS_FIELDS = ['total_assets', 'total_equity', 'total_liabilities', 'total_investments',
             'cash_and_cash_equivalents']
IS_FIELDS = ['gross_premiums_written', 'net_premiums_earned', 'net_investment_income',
             'net_income', 'total_revenues', 'total_expenses', 'losses_and_lae']

def get_field(section_data, *keys):
    """Try multiple key variations."""
    if not isinstance(section_data, dict):
        return None
    for k in keys:
        for actual_key, v in section_data.items():
            if actual_key.lower().replace(' ','_').replace('/','_').replace('&','and') == k.replace('/','_').replace('&','and'):
                if v not in (None, '', 0, '0'):
                    return v
    return None

print("=" * 100)
print("EXTRACTION COMPARISON REPORT — DUMMY vs CLAUDE-DATA")
print("=" * 100)

replaceable = []
partial = []
not_found = []

for company in ALL_TARGETS:
    ext_data = find_in_extracted(company)
    is_dummy = company in DUMMY_COMPANIES

    if not ext_data:
        not_found.append(company)
        continue

    years_available = sorted(ext_data.keys())
    results = {}

    for year in [2023, 2024]:
        if year not in ext_data:
            results[year] = None
            continue
        ydata = ext_data[year]
        bs = ydata.get('balance_sheet', {})
        inc = ydata.get('income_statement', {})

        # Check key metrics
        fields_found = {}
        for section, fields in [('BS', bs), ('IS', inc)]:
            for k, v in fields.items():
                if v not in (None, '', 0, '0', 0.0):
                    fields_found[k] = v

        results[year] = fields_found

    # Assess quality
    has_2024 = results.get(2024) and len(results[2024]) >= 4
    has_2023 = results.get(2023) and len(results[2023]) >= 4
    fields_2024 = len(results.get(2024) or {})
    fields_2023 = len(results.get(2023) or {})

    status = '🟢 REPLACEABLE' if (has_2024 or has_2023) else '🟡 PARTIAL'
    if fields_2024 == 0 and fields_2023 == 0:
        status = '🔴 EMPTY'

    print(f"\n{'[DUMMY]' if is_dummy else '[ZERO]':8} {company}")
    print(f"  Extracted years available: {years_available}")
    print(f"  2024 fields with data: {fields_2024}  | 2023 fields: {fields_2023}")
    print(f"  Status: {status}")

    if results.get(2024):
        # Show key values
        for k in ['Total Assets', 'Total Equity', 'Net Premiums Earned', 'Net Income']:
            for actual, v in results[2024].items():
                if k.lower() in actual.lower():
                    print(f"    2024 {k}: {v}")
                    break

    if status == '🟢 REPLACEABLE':
        replaceable.append((company, years_available, fields_2024, fields_2023))
    elif status == '🟡 PARTIAL':
        partial.append((company, years_available, fields_2024, fields_2023))
    else:
        not_found.append(company)

print(f"\n{'=' * 100}")
print(f"SUMMARY")
print(f"{'=' * 100}")
print(f"🟢 Can replace immediately:  {len(replaceable)} companies")
for c, yrs, f24, f23 in replaceable:
    print(f"   - {c}  (years: {yrs}, fields: 2024={f24}, 2023={f23})")
print(f"\n🟡 Partial data available:  {len(partial)} companies")
for c, yrs, f24, f23 in partial:
    print(f"   - {c}  (years: {yrs}, fields: 2024={f24}, 2023={f23})")
print(f"\n🔴 Not in extracted data:   {len(not_found)} companies")
for c in not_found:
    print(f"   - {c}")
