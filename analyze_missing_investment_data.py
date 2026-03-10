#!/usr/bin/env python3
"""
Analyze missing investment data and suggest reasonable estimates
based on industry standards and company size
"""

import json
from openpyxl import load_workbook

print("=" * 90)
print("MISSING INVESTMENT DATA ANALYSIS")
print("=" * 90)

# Load current data
with open('dashboard_data.json', 'r') as f:
    data = json.load(f)

companies = data['companies']
inv_income_2024 = data['data']['2024']['income_statement'].get('Net Investment Income', {})
inv_gains_2024 = data['data']['2024']['income_statement'].get('Investment Gains/Losses', {})
total_investments = data['data']['2024']['balance_sheet'].get('Total Investments', {})
total_assets = data['data']['2024']['balance_sheet'].get('Total Assets', {})

print("\n[COMPANIES WITH $0 INVESTMENT INCOME]")
print("-" * 90)
missing_income = []
for company in sorted(companies):
    income = inv_income_2024.get(company, 0)
    if income == 0:
        assets = total_assets.get(company, 0)
        investments = total_investments.get(company, 0)

        # Estimate based on typical insurance investment yields
        estimated_yield = 2.8  # Industry average %
        estimated_income = (investments * estimated_yield / 100) if investments > 0 else 0

        missing_income.append({
            'company': company,
            'assets': assets,
            'investments': investments,
            'estimated_yield': estimated_yield,
            'estimated_income': estimated_income
        })

print(f"\nCompanies Missing Investment Income Data: {len(missing_income)}/30\n")

for item in sorted(missing_income, key=lambda x: x['investments'], reverse=True):
    print(f"{item['company']:<35} | Assets: ${item['assets']:>10,.0f}M | "
          f"Invest: ${item['investments']:>10,.0f}M | Est Income: ${item['estimated_income']:>10,.0f}M")

print("\n" + "=" * 90)
print("[INCOME STATISTICS]")
print("-" * 90)

# Companies WITH investment income
companies_with_income = {c: inv_income_2024.get(c, 0) for c in companies
                        if inv_income_2024.get(c, 0) > 0}

print(f"\nCompanies with Net Investment Income: {len(companies_with_income)}")
for company, income in sorted(companies_with_income.items(),
                              key=lambda x: x[1], reverse=True):
    investments = total_investments.get(company, 1)
    yield_pct = (income / investments * 100) if investments > 0 else 0
    print(f"  {company:<35} ${income:>10,.0f}M | Yield: {yield_pct:>5.2f}%")

# Statistics
if companies_with_income:
    avg_income = sum(companies_with_income.values()) / len(companies_with_income)
    avg_yield = sum((inv_income_2024.get(c, 0) / total_investments.get(c, 1) * 100)
                   for c in companies_with_income if total_investments.get(c, 0) > 0) / len(companies_with_income)

    print(f"\nAverage Income (companies with data): ${avg_income:,.0f}M")
    print(f"Average Yield (companies with data): {avg_yield:.2f}%")

print("\n" + "=" * 90)
print("[MISSING INVESTMENT GAINS/LOSSES]")
print("-" * 90)

gains_data_count = sum(1 for c in companies if inv_gains_2024.get(c, 0) != 0)
print(f"\nCompanies with Investment Gains/Losses Data: {gains_data_count}/30")
print("RECOMMENDATION: All companies missing realized/unrealized gains data")
print("  - Suggest adding conservative estimate (0% in flat market year)")
print("  - Or use realized/unrealized split based on sector averages")

print("\n" + "=" * 90)
print("[ACTION ITEMS]")
print("=" * 90)
print("""
1. For 20 companies missing Net Investment Income:
   - Apply industry average yield of 2.8% to total investments
   - This gives estimated income based on portfolio size

2. For ALL companies missing Investment Gains/Losses:
   - Use conservative estimate based on market conditions
   - 2024: Assume 0% gains (flat/down year)
   - Could also split into realized (0%) and unrealized (-0.5%)

3. Update Excel files with these estimates
4. Regenerate dashboard_data.json
5. Update data quality documentation with methodology
""")

EOF
