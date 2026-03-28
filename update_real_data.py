"""
Update dashboard_data.json with real extracted values.
Uses precise field matching per company.
"""
import json, re

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

with open(r'C:\Users\nthig\.openclaw\workspace\claude-data\bma-filings\data\extracted_financials.json',
          encoding='utf-8', errors='replace') as f:
    extracted = json.load(f)

# ── Helpers ─────────────────────────────────────────────────────────────────
def parse_millions(v):
    """Return value in millions. Raw values > 1M are treated as raw dollars."""
    if v is None or v in ('', 'N/A'): return None
    try:
        fv = float(str(v).replace(',', '').strip())
        if fv == 0: return None
        return round(fv / 1_000_000, 1) if abs(fv) > 1_000_000 else round(fv, 1)
    except: return None

def find_field(section_dict, *patterns, exact=False, exclude=None):
    """Find first key containing any pattern (case-insensitive) and return parsed value."""
    if not isinstance(section_dict, dict): return None
    for raw_k, raw_v in section_dict.items():
        k_lower = raw_k.lower()
        if exclude and any(ex.lower() in k_lower for ex in exclude):
            continue
        for pat in patterns:
            if exact:
                if k_lower.split()[0:len(pat.split())] == pat.lower().split():
                    v = parse_millions(raw_v)
                    if v: return v
            else:
                if pat.lower() in k_lower:
                    v = parse_millions(raw_v)
                    if v: return v
    return None

def set_val(company, year, section, metric, value):
    if value is None: return False
    yr = str(year)
    if yr in dash['data'] and section in dash['data'][yr] and metric in dash['data'][yr][section]:
        dash['data'][yr][section][metric][company] = value
        return True
    return False

def recalc_ratios(company, year):
    yr = str(year)
    d = dash['data'][yr]
    bs, inc, rat = d['balance_sheet'], d['income_statement'], d['ratios']
    def g(s, k): return s.get(k, {}).get(company, 0) or 0

    net_income   = g(inc, 'Net Income')
    total_equity = g(bs, 'Total Equity')
    total_assets = g(bs, 'Total Assets')
    net_premiums = g(inc, 'Net Premiums Earned')
    losses       = abs(g(inc, 'Losses and LAE'))   # stored as negative
    expenses     = abs(g(inc, 'Total Expenses'))
    net_inv_inc  = g(inc, 'Net Investment Income')
    inv_gains    = g(inc, 'Investment Gains/Losses')
    total_inv    = g(bs, 'Total Investments')

    def safe(num, den, dp=1): return round(num / den * 100, dp) if den else 0

    rat['ROE (%)'][company]                   = safe(net_income, total_equity)
    rat['ROA (%)'][company]                   = safe(net_income, total_assets)
    rat['Equity Ratio (%)'][company]          = safe(total_equity, total_assets)
    rat['Loss Ratio (%)'][company]            = safe(losses, net_premiums)
    rat['Expense Ratio (%)'][company]         = safe(expenses, net_premiums)
    rat['Combined Ratio (%)'][company]        = safe(losses + expenses, net_premiums)
    rat['Investment Return (%)'][company]     = round(safe(net_inv_inc + inv_gains, total_inv, dp=2), 2)
    rat['Investment Yield (%)'][company]      = round(safe(net_inv_inc, total_inv, dp=2), 2)
    rat['Investments to Assets (%)'][company] = safe(total_inv, total_assets)

# ── STEP 1: MS Amlin AG (full real data, both years) ────────────────────────
print("\n=== MS Amlin AG ===")
for year in [2023, 2024]:
    key = f'MS Amlin AG - {year}'
    data = extracted.get(key, {})
    bs   = data.get('balance_sheet', {})
    inc  = data.get('income_statement', {})

    updates = {
        ('balance_sheet',   'Total Assets'):             find_field(bs, 'total assets', exclude=['and equity']),
        ('balance_sheet',   'Total Equity'):             find_field(bs, 'total equity', exclude=['and']),
        ('balance_sheet',   'Total Liabilities'):        find_field(bs, 'total liabilities', exclude=['and equity']),
        ('balance_sheet',   'Total Investments'):        find_field(bs, 'investments', exclude=['reinsurers', 'derivative', 'net']),
        ('income_statement','Gross Premiums Written'):   find_field(inc, 'gross premium written'),
        ('income_statement','Net Premiums Earned'):      find_field(inc, 'net premiums earned'),
        ('income_statement','Net Investment Income'):    find_field(inc, 'net income from investments', 'net investment income'),
        ('income_statement','Net Income'):               find_field(inc, 'profit for the year', 'profit/(loss) for the year', 'net profit', exclude=['investments', 'ceded', 'technical', 'brought forward', 'share', 'loss']) or find_field(inc, 'profit', exclude=['brought forward', 'investments', 'ceded', 'technical', 'share', 'loss carried', 'underwriting']),
        ('income_statement','Losses and LAE'):           find_field(inc, 'net claims and claim expenses incurred', 'net claims incurred'),
        ('income_statement','Total Revenues'):           find_field(inc, 'total technical income', 'total revenues', 'total income'),
        ('income_statement','Total Expenses'):           find_field(inc, 'total charges', 'total technical charges', 'total expenses', exclude=['income', 'revenue']),
    }

    applied = 0
    for (section, metric), value in updates.items():
        if set_val('MS Amlin AG', year, section, metric, value):
            print(f"  {year} {metric}: {value}")
            applied += 1
    recalc_ratios('MS Amlin AG', year)
    print(f"  {year}: {applied} fields set")

# ── STEP 2: Flag pending companies ──────────────────────────────────────────
EMPTY_PENDING = [
    'Hiscox Insurance Company Bermuda', 'Starr Insurance & Reinsurance',
    'Fortitude Reinsurance Company', 'SiriusPoint Bermuda Insurance',
    'Conduit Reinsurance', 'Liberty Specialty Markets Bermuda', 'Hamilton Re',
    'American International Reinsurance Company Ltd.',
    'Brit Reinsurance Bermuda Limited', 'Fortitude International Reinsurance Ltd.',
    'Lancashire Insurance Company', 'XL Bermuda', 'AXA XL Reinsurance',
    'Endurance Specialty Insurance', 'Validus Reinsurance', 'Somers Re',
    'Canopius Reinsurance', 'Fidelis Insurance Bermuda', 'Argo Re Ltd.',
]
dash['data_pending'] = EMPTY_PENDING
print(f"\nFlagged {len(EMPTY_PENDING)} companies as data_pending")

# ── Save ─────────────────────────────────────────────────────────────────────
with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(dash, f, separators=(',', ':'))
print("\ndashboard_data.json saved.")

# ── Sanity check ─────────────────────────────────────────────────────────────
print("\nSANITY CHECK — MS Amlin 2024:")
for section in ['balance_sheet', 'income_statement', 'ratios']:
    for metric, vals in dash['data']['2024'][section].items():
        v = vals.get('MS Amlin AG', None)
        if v and v != 0:
            print(f"  {section}.{metric}: {v}")
