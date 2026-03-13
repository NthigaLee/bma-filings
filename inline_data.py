import json, re

with open('dashboard_data.json') as f:
    data = json.load(f)

new_data_js = 'var dashboardData = ' + json.dumps(data, separators=(',',':')) + ';'

with open('dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Pattern 1: existing inline var dashboardData = {...};
pattern1 = r'var dashboardData = \{.*?\};'
if re.search(pattern1, html, re.DOTALL):
    html = re.sub(pattern1, new_data_js, html, flags=re.DOTALL)
    print('Replaced inline dashboardData')
# Pattern 2: external script tag
elif re.search(r'<script src="dashboard_data\.js[^"]*"></script>', html):
    html = re.sub(r'<script src="dashboard_data\.js[^"]*"></script>',
                  f'<script>\n    {new_data_js}\n    </script>', html)
    print('Replaced external script tag')
else:
    print('ERROR: no data injection point found')

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'dashboard.html written: {len(html):,} chars | data: {len(new_data_js):,} chars')
