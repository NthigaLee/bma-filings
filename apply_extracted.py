"""
Apply extracted data + tag estimated companies on the dashboard.
Only uses values that pass sanity checks (sensible ranges for Bermuda re/insurers).
"""
import json, re

with open('fast_extract_results.json') as f:
    raw = json.load(f)

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

# ── Sanity bounds (in millions USD) ─────────────────────────────────────────
# Total Assets: 500M – 200,000M  |  NPE: 50M – 20,000M  |  NI: -5,000M – 10,000M
def sane(val, lo, hi):
    return val is not None and lo <= val <= hi

def clean_fields(bs, is_):
    """Return only sanity-checked fields."""
    out_bs, out_is = {}, {}
    if sane(bs.get('Total Assets'), 200, 200_000):
        out_bs['Total Assets'] = bs['Total Assets']
    if sane(bs.get('Total Equity'), 50, 80_000):
        out_bs['Total Equity'] = bs['Total Equity']
    if sane(bs.get('Total Liabilities'), 100, 200_000):
        out_bs['Total Liabilities'] = bs['Total Liabilities']
    if sane(bs.get('Total Investments'), 50, 150_000):
        out_bs['Total Investments'] = bs['Total Investments']
    if sane(is_.get('Gross Premiums Written'), 50, 30_000):
        out_is['Gross Premiums Written'] = is_['Gross Premiums Written']
    if sane(is_.get('Net Premiums Earned'), 50, 25_000):
        out_is['Net Premiums Earned'] = is_['Net Premiums Earned']
    if sane(is_.get('Net Investment Income'), 1, 10_000):
        out_is['Net Investment Income'] = is_['Net Investment Income']
    if sane(is_.get('Net Income'), -10_000, 10_000):
        out_is['Net Income'] = is_['Net Income']
    if sane(is_.get('Losses and LAE'), 10, 30_000):
        out_is['Losses and LAE'] = is_.get('Losses and LAE')
    if sane(is_.get('Total Expenses'), 10, 50_000):
        out_is['Total Expenses'] = is_.get('Total Expenses')
    return out_bs, out_is

def set_val(company, year, section, metric, value):
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
    ta   = g(bs,  'Total Assets');   te  = g(bs, 'Total Equity')
    ti   = g(bs,  'Total Investments')
    npe  = g(inc, 'Net Premiums Earned');  ni  = g(inc, 'Net Income')
    loss = abs(g(inc, 'Losses and LAE')); exp = abs(g(inc, 'Total Expenses'))
    nii  = g(inc, 'Net Investment Income')
    def safe(n, d, dp=1): return round(n/d*100, dp) if d else 0
    rat['ROE (%)'][company]                   = safe(ni, te)
    rat['ROA (%)'][company]                   = safe(ni, ta)
    rat['Equity Ratio (%)'][company]          = safe(te, ta)
    rat['Loss Ratio (%)'][company]            = safe(loss, npe)
    rat['Expense Ratio (%)'][company]         = safe(exp, npe)
    rat['Combined Ratio (%)'][company]        = safe(loss + exp, npe)
    rat['Investment Return (%)'][company]     = round(safe(nii, ti, dp=2), 2)
    rat['Investment Yield (%)'][company]      = round(safe(nii, ti, dp=2), 2)
    rat['Investments to Assets (%)'][company] = safe(ti, ta)

# ── Apply ────────────────────────────────────────────────────────────────────
updated = {}
estimated = []

print("APPLYING EXTRACTED DATA\n" + "="*70)
for company, year_data in raw.items():
    company_updated = False
    for year_str, data in year_data.items():
        year = int(year_str)
        if not isinstance(data, dict) or 'bs' not in data:
            continue
        bs_clean, is_clean = clean_fields(data['bs'], data['is'])
        if not bs_clean and not is_clean:
            continue
        n = 0
        for metric, value in bs_clean.items():
            if set_val(company, year, 'balance_sheet', metric, value): n += 1
        for metric, value in is_clean.items():
            if set_val(company, year, 'income_statement', metric, value): n += 1
        if n > 0:
            recalc_ratios(company, year)
            print(f"  {company} {year}: {n} fields → BS:{list(bs_clean.keys())} IS:{list(is_clean.keys())}")
            company_updated = True
    if company_updated:
        updated[company] = True
    else:
        estimated.append(company)

# ── Tag estimated companies ──────────────────────────────────────────────────
# Companies still with no real data get an "estimated" flag
# Also keep the ones from the previous data_pending list that weren't updated
existing_pending = set(dash.get('data_pending', []))
still_estimated = sorted(set(estimated) | (existing_pending - set(updated.keys())))
dash['data_pending'] = sorted(still_estimated)
dash['data_sourced'] = sorted(updated.keys())

print(f"\n✅ Updated with real data: {len(updated)} companies")
for c in sorted(updated.keys()):
    print(f"   - {c}")

print(f"\n⚠️  Marked as 'Estimated': {len(still_estimated)} companies")
for c in still_estimated:
    print(f"   - {c}")

# ── Save ─────────────────────────────────────────────────────────────────────
with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(dash, f, separators=(',', ':'))
print("\ndashboard_data.json saved.")
