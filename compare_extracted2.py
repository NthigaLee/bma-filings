"""
Accurate comparison using manual name mapping
"""
import json, re
from collections import defaultdict

# Manual mapping: dashboard name -> extracted name(s)
NAME_MAP = {
    'XL Bermuda':                                   'XL Bermuda Ltd',
    'AXA XL Reinsurance':                           'AXA XL Reinsurance Ltd',
    'Endurance Specialty Insurance':                'Endurance Specialty Insurance Ltd.',
    'Validus Reinsurance':                          'Validus Reinsurance Ltd.',
    'Hiscox Insurance Company Bermuda':             'Hiscox Insurance Company Bermuda Limited',
    'Starr Insurance & Reinsurance':                'Starr Insurance Reinsurance Limited',
    'Fortitude Reinsurance Company':                'Fortitude Reinsurance Company Ltd.',
    'SiriusPoint Bermuda Insurance':                'SiriusPoint Bermuda Insurance Company Ltd.',
    'Somers Re':                                    'Somers Re Ltd.',
    'MS Amlin AG':                                  'MS Amlin AG',
    'Lancashire Insurance Company':                 'Lancashire Insurance Company Limited',
    'Conduit Reinsurance':                          'Conduit Reinsurance Limited',
    'Liberty Specialty Markets Bermuda':            'Liberty Specialty Markets Bermuda Limited',
    'Canopius Reinsurance':                         'Canopius Reinsurance Limited',
    'Hamilton Re':                                  'Hamilton Re Ltd.',
    'Fidelis Insurance Bermuda':                    'Fidelis Insurance Bermuda Limited',
    # Zeros
    'American International Reinsurance Company Ltd.': 'American International Reinsurance Company Ltd.',
    'Argo Re Ltd.':                                 'Argo Re Ltd.',
    'Brit Reinsurance Bermuda Limited':             'Brit Reinsurance Bermuda Limited',
    'Fortitude International Reinsurance Ltd.':     'Fortitude International Reinsurance Ltd.',
}

DUMMY_COMPANIES = list(NAME_MAP.keys())[:16]
ZERO_COMPANIES = list(NAME_MAP.keys())[16:]

with open(r'C:\Users\nthig\.openclaw\workspace\claude-data\bma-filings\data\extracted_financials.json', encoding='utf-8', errors='replace') as f:
    extracted = json.load(f)

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

# Build lookup by extracted name + year
ext_by_name_year = {}
for key, val in extracted.items():
    m = re.match(r'^(.+?)\s*-\s*(\d{4})$', key)
    if m:
        name = m.group(1).strip()
        year = int(m.group(2))
        if name not in ext_by_name_year:
            ext_by_name_year[name] = {}
        ext_by_name_year[name][year] = val

KEY_BS  = ['Total Assets', 'Total Equity', 'Total Liabilities', 'Total Investments', 'Cash and Cash Equivalents']
KEY_IS  = ['Gross Premiums Written', 'Net Premiums Earned', 'Net Investment Income', 'Net Income', 'Total Revenues', 'Total Expenses', 'Losses and LAE']

def count_real_fields(section):
    """Count non-zero, non-None fields."""
    if not isinstance(section, dict): return 0
    return sum(1 for v in section.values() if v not in (None, 0, 0.0, '', 'N/A'))

def get_val(section, *names):
    if not isinstance(section, dict): return None
    for name in names:
        for k, v in section.items():
            if k.lower().strip() == name.lower().strip():
                if v not in (None, 0, 0.0, ''):
                    return v
    return None

print("=" * 100)
print("EXTRACTION COMPARISON REPORT")
print("=" * 100)

replaceable = []
partial = []
empty = []

for dash_name, ext_name in NAME_MAP.items():
    is_dummy = dash_name in DUMMY_COMPANIES
    tag = '[DUMMY]' if is_dummy else '[ZERO] '

    ext_data = ext_by_name_year.get(ext_name, {})
    years_avail = sorted(ext_data.keys())

    report = {}
    for year in [2023, 2024]:
        if year not in ext_data:
            report[year] = {'bs_fields': 0, 'is_fields': 0, 'bs': {}, 'is': {}}
            continue
        ydata = ext_data[year]
        bs = ydata.get('balance_sheet', {})
        inc = ydata.get('income_statement', {})
        report[year] = {
            'bs_fields': count_real_fields(bs),
            'is_fields': count_real_fields(inc),
            'bs': bs,
            'is': inc
        }

    f24_bs = report[2024]['bs_fields']
    f24_is = report[2024]['is_fields']
    f23_bs = report[2023]['bs_fields']
    f23_is = report[2023]['is_fields']
    total_24 = f24_bs + f24_is
    total_23 = f23_bs + f23_is

    # Current dashboard values (dummy)
    curr_assets = dash['data']['2024']['balance_sheet']['Total Assets'].get(dash_name, 0)
    curr_equity = dash['data']['2024']['balance_sheet']['Total Equity'].get(dash_name, 0)

    # Extracted values
    ext_assets_24 = get_val(report[2024]['bs'], 'Total Assets', 'Total assets')
    ext_equity_24 = get_val(report[2024]['bs'], 'Total Equity', "Shareholders' equity", 'Total equity')
    ext_npe_24    = get_val(report[2024]['is'], 'Net Premiums Earned', 'Net premiums earned')
    ext_ni_24     = get_val(report[2024]['is'], 'Net Income', 'Net income', 'Net earnings')

    if total_24 >= 6 or total_23 >= 6:
        status = 'REPLACEABLE'
        replaceable.append(dash_name)
    elif total_24 >= 2 or total_23 >= 2:
        status = 'PARTIAL'
        partial.append(dash_name)
    else:
        status = 'EMPTY'
        empty.append(dash_name)

    marker = 'YES' if status == 'REPLACEABLE' else ('~' if status == 'PARTIAL' else 'NO')
    print(f"\n{tag}  {dash_name}")
    print(f"  Extracted name: {ext_name}")
    print(f"  Years in extract: {years_avail}")
    print(f"  Fields 2024 → BS:{f24_bs} IS:{f24_is} total={total_24}  |  2023 → BS:{f23_bs} IS:{f23_is} total={total_23}")
    print(f"  Current (dummy)  Assets={curr_assets:>10,.0f}   Equity={curr_equity:>10,.0f}")
    if ext_assets_24:
        print(f"  Extracted 2024   Assets={ext_assets_24:>10,.0f}   Equity={ext_equity_24 or 0:>10,.0f}   NPE={ext_npe_24 or 0:>10,.0f}   NI={ext_ni_24 or 0:>10,.0f}")
    print(f"  >>> CAN REPLACE: {marker}")

print(f"\n{'=' * 100}")
print(f"SUMMARY")
print(f"{'=' * 100}")
print(f"REPLACEABLE ({len(replaceable)}): {replaceable}")
print(f"PARTIAL     ({len(partial)}): {partial}")
print(f"EMPTY       ({len(empty)}): {empty}")
