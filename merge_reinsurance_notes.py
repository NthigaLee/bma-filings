"""
merge_reinsurance_notes.py — Merge reinsurance note data into dashboard_data.json.
- Adds reinsurance_note section per company-year
- Updates Net Premiums Written in income_statement if missing/null
- Does NOT overwrite Gross Premiums Written if cross-check fails (>5% mismatch)
- Regenerates dashboard_data.js
"""
import json, re
from pathlib import Path

EXTRACTED = Path('reinsurance_notes_extracted.json')
DASHBOARD_JSON = Path('dashboard_data.json')
DASHBOARD_JS = Path('dashboard_data.js')

# Reinsurance note fields to include in dashboard
NOTE_FIELDS = [
    'assumed_premiums_written',
    'ceded_premiums_written',
    'net_premiums_written',
    'assumed_premiums_earned',
    'ceded_premiums_earned',
    'net_premiums_earned',
    'assumed_losses_paid',
    'ceded_losses_recovered',
    'net_losses_incurred',
    'extraction_status',
    'source_pdf',
]

extracted = json.loads(EXTRACTED.read_text(encoding='utf-8'))
dashboard = json.loads(DASHBOARD_JSON.read_text(encoding='utf-8'))
data = dashboard['data']

merged_count = 0
npw_updated = 0
skipped_gpw = 0

for company, years_data in extracted.items():
    for year_str, result in years_data.items():
        status = result.get('extraction_status', 'not_found')
        if status not in ('success', 'partial'):
            continue

        year = str(year_str)
        if year not in data:
            continue

        # Build reinsurance_note record (only defined fields)
        note = {}
        for field in NOTE_FIELDS:
            v = result.get(field)
            if v is not None:
                note[field] = v

        if not note:
            continue

        # Ensure reinsurance_note section exists in this year
        if 'reinsurance_note' not in data[year]:
            data[year]['reinsurance_note'] = {}

        data[year]['reinsurance_note'][company] = note
        merged_count += 1

        # Update Net Premiums Written in income_statement if missing/null
        is_section = data[year].get('income_statement', {})
        npw_val = result.get('net_premiums_written')
        if npw_val is not None:
            existing_npw = is_section.get('Net Premiums Written', {}).get(company)
            if not existing_npw:
                if 'Net Premiums Written' not in is_section:
                    is_section['Net Premiums Written'] = {}
                is_section['Net Premiums Written'][company] = npw_val
                npw_updated += 1

        # Check if we should update GPW (only if match or no_prior_data)
        cc_result = result.get('cross_check_result', '')
        apw = result.get('assumed_premiums_written')
        if apw is not None and cc_result in ('match', 'no_prior_data'):
            # Only set GPW if no_prior_data (don't overwrite existing matched values)
            if cc_result == 'no_prior_data':
                gpw_metric = is_section.get('Gross Premiums Written', {})
                if not gpw_metric.get(company):
                    if 'Gross Premiums Written' not in is_section:
                        is_section['Gross Premiums Written'] = {}
                    is_section['Gross Premiums Written'][company] = apw
        elif cc_result == 'mismatch':
            skipped_gpw += 1

print(f"Merged: {merged_count} company-year records into reinsurance_note sections")
print(f"Net Premiums Written updated: {npw_updated}")
print(f"GPW overwrites skipped (mismatch): {skipped_gpw}")

# Write updated dashboard_data.json
DASHBOARD_JSON.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"Wrote {DASHBOARD_JSON}")

# Regenerate dashboard_data.js
js_content = f"window.BMA_DASHBOARD_DATA = {json.dumps(dashboard, indent=2, ensure_ascii=False)};\n"
DASHBOARD_JS.write_text(js_content, encoding='utf-8')
print(f"Wrote {DASHBOARD_JS}")
