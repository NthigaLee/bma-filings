import json

with open('dashboard_data.json') as f:
    dash = json.load(f)

companies = dash['companies']
data_2024 = dash['data']['2024']

# A company has "dummy" data if its values are suspiciously round (multiples of 50 or 100)
# and/or identical to other companies' values

def is_round(val, threshold=50):
    """True if value is a non-zero multiple of threshold - sign of estimated/dummy data."""
    if val == 0:
        return False
    return val % threshold == 0

def check_company(company):
    flags = []

    # Key metrics to check
    metrics = {
        'balance_sheet': ['Total Assets', 'Total Equity', 'Total Investments', 'Total Liabilities'],
        'income_statement': ['Net Premiums Earned', 'Net Income', 'Total Revenues', 'Gross Premiums Written'],
    }

    all_round = 0
    non_zero = 0
    values_seen = []

    for section, fields in metrics.items():
        for field in fields:
            val = data_2024.get(section, {}).get(field, {}).get(company, 0)
            if val != 0:
                non_zero += 1
                values_seen.append((field, val))
                if is_round(val, 50):
                    all_round += 1

    # Check if Total Assets is very round (e.g. 9100, 7850, exactly divisible by 100)
    total_assets = data_2024['balance_sheet']['Total Assets'].get(company, 0)
    total_equity = data_2024['balance_sheet']['Total Equity'].get(company, 0)
    net_income = data_2024['income_statement']['Net Income'].get(company, 0)

    # Heuristic: if ALL non-zero values are round multiples of 50, likely dummy
    if non_zero > 0 and all_round == non_zero:
        flags.append('ALL_VALUES_ROUND_50')

    # Check if ratios match exactly with suspiciously uniform pattern
    roe = dash['data']['2024']['ratios']['ROE (%)'].get(company, 0)
    equity_ratio = dash['data']['2024']['ratios']['Equity Ratio (%)'].get(company, 0)

    # Many dummy companies have equity ratio exactly 51.x%
    if 51.0 <= equity_ratio <= 52.5 and equity_ratio != 0:
        flags.append(f'EQUITY_RATIO_SUSPICIOUS={equity_ratio}')

    return {
        'company': company,
        'total_assets': total_assets,
        'total_equity': total_equity,
        'net_income': net_income,
        'roe': roe,
        'equity_ratio': equity_ratio,
        'non_zero_fields': non_zero,
        'round_fields': all_round,
        'flags': flags
    }

# Categorise companies
print("=" * 80)
print("LIKELY DUMMY / ESTIMATED DATA:")
print("=" * 80)
dummy = []
real = []

for company in companies:
    result = check_company(company)
    # Dummy if all values are round multiples of 50
    if 'ALL_VALUES_ROUND_50' in result['flags'] and result['non_zero_fields'] > 0:
        dummy.append(result)
    elif result['non_zero_fields'] == 0:
        result['flags'].append('ALL_ZEROS')
        dummy.append(result)
    else:
        real.append(result)

for r in sorted(dummy, key=lambda x: x['total_assets'], reverse=True):
    print(f"  {r['company']:<45} Assets={r['total_assets']:>8,.0f}  Equity={r['total_equity']:>8,.0f}  Flags={r['flags']}")

print(f"\n{'=' * 80}")
print("LIKELY REAL EXTRACTED DATA:")
print("=" * 80)
for r in sorted(real, key=lambda x: x['total_assets'], reverse=True):
    print(f"  {r['company']:<45} Assets={r['total_assets']:>8,.1f}  ROE={r['roe']:>5.1f}%  EquityR={r['equity_ratio']:>5.1f}%")

print(f"\nSummary: {len(dummy)} likely dummy/zero, {len(real)} likely real")
