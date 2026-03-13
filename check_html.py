with open('dashboard.html', encoding='utf-8') as f:
    content = f.read()

checks = [
    'Comparative financial analysis of 40 Bermuda',
    'company-filter-trigger',
    'filter-panel-body',
    'filterCompanyList',
    'industry-avg-row',
    'getCategoryForMetric',
    'updateFilterTriggerLabel',
    'comparison-table tr.industry-avg-row',
    'background: #ffffff !important',
    'background: #fff0f3 !important',
]
all_ok = True
for c in checks:
    found = c in content
    status = 'OK' if found else 'MISSING'
    if not found:
        all_ok = False
    print(f'[{status}] {c}')

print(f'\nFile size: {len(content):,} chars')
print('All checks passed!' if all_ok else 'SOME CHECKS FAILED')
