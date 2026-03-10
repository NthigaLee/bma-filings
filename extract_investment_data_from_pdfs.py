#!/usr/bin/env python3
"""
Extract comprehensive investment data from PDF financial statements
Searches for:
- Net Investment Income
- Realized Gains/Losses
- Unrealized Gains/Losses
- Investment Income Components
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

try:
    import pdfplumber
except ImportError:
    print("[ERROR] pdfplumber not installed. Installing...")
    os.system("pip install pdfplumber")
    import pdfplumber

print("=" * 90)
print("EXTRACTING INVESTMENT DATA FROM PDF FINANCIAL STATEMENTS")
print("=" * 90)

# Company mapping for matching PDFs
COMPANY_NAMES = [
    'Arch Reinsurance', 'Ascot Bermuda', 'Aspen Bermuda', 'AXIS Specialty',
    'Chubb Tempest Reinsurance', 'Everest Reinsurance Bermuda', 'Hannover Re Bermuda',
    'Markel Bermuda', 'Partner Reinsurance Company', 'Renaissance Reinsurance',
    'Endurance Specialty Insurance', 'XL Bermuda', 'AXA XL Reinsurance', 'Validus Reinsurance',
    'Somers Re', 'Lancashire Insurance Company', 'Hiscox Insurance Company Bermuda',
    'Canopius Reinsurance', 'Conduit Reinsurance', 'Fidelis Insurance Bermuda',
    'Fortitude Reinsurance Company', 'Group Ark Insurance', 'Hamilton Re', 'Harrington Re',
    'Liberty Specialty Markets Bermuda', 'MS Amlin AG', 'Premia Reinsurance',
    'Starr Insurance & Reinsurance', 'Vantage Risk', 'SiriusPoint Bermuda Insurance'
]

# Keywords to search for investment-related items
INVESTMENT_KEYWORDS = {
    'net_investment_income': [
        'net investment income', 'net investment gain', 'investment income',
        'interest income', 'dividend income', 'rental income'
    ],
    'realized_gains': [
        'realized gains', 'realized gain', 'gains on sale',
        'profit on investments', 'gains realized'
    ],
    'unrealized_gains': [
        'unrealized gains', 'unrealized gain', 'unrealized appreciation',
        'mark-to-market gains', 'fair value gains'
    ],
    'investment_losses': [
        'investment losses', 'investment loss', 'loss on investments',
        'realized losses', 'unrealized losses'
    ]
}

extraction_results = defaultdict(lambda: {
    '2023': {},
    '2024': {}
})

def extract_pdf_investment_data(pdf_path):
    """Extract investment data from a single PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            tables = []

            # Extract text and tables from first 10 pages (income statement usually early)
            for page_num, page in enumerate(pdf.pages[:10]):
                text += page.extract_text() or ""
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)

            return text, tables
    except Exception as e:
        print(f"  [ERROR] Could not read PDF: {e}")
        return "", []

def find_investment_values_in_text(text):
    """Search text for investment income/gains values"""
    results = {}

    # Find number patterns (can be $1000, 1,000, 1000M, etc.)
    number_pattern = r'[\$]?[\s]*([\d,]+(?:\.\d+)?)\s*(?:M|million)?'

    for category, keywords in INVESTMENT_KEYWORDS.items():
        for keyword in keywords:
            # Case-insensitive search with context
            pattern = rf'({keyword}).*?({number_pattern})'
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)

            for match in matches:
                try:
                    value_str = match.group(2).replace(',', '')
                    value = float(value_str)
                    if 0 <= value <= 100000:  # Reasonable range for investment values
                        results[category] = value
                        break
                except:
                    continue

    return results

def find_year_in_text(text):
    """Try to determine year from PDF text"""
    if '2024' in text[:500] or '2024' in text[-500:]:
        return '2024'
    elif '2023' in text[:500] or '2023' in text[-500:]:
        return '2023'
    return '2024'  # Default

# Process all PDFs
pdf_dir = Path('pdfs')
pdf_files = sorted(pdf_dir.glob('*.pdf'))

print(f"\nFound {len(pdf_files)} PDF files to process")
print("\nExtracting investment data from PDFs...\n")

for i, pdf_path in enumerate(pdf_files, 1):
    filename = pdf_path.name

    # Try to match company from filename
    matched_company = None
    for company in COMPANY_NAMES:
        if company.split()[0].lower() in filename.lower():
            matched_company = company
            break

    if not matched_company:
        # Try partial match
        for company in COMPANY_NAMES:
            if any(part.lower() in filename.lower() for part in company.split()):
                matched_company = company
                break

    if matched_company:
        print(f"[{i:3d}/{len(pdf_files)}] {filename[:60]:<60} -> {matched_company}")

        text, tables = extract_pdf_investment_data(pdf_path)

        if text:
            year = find_year_in_text(text)
            investment_data = find_investment_values_in_text(text)

            if investment_data:
                print(f"      Year: {year} | Found: {list(investment_data.keys())}")
                extraction_results[matched_company][year].update(investment_data)
            else:
                print(f"      Year: {year} | No investment data found in text")

print("\n" + "=" * 90)
print("EXTRACTION RESULTS")
print("=" * 90)

# Save results
results_file = 'investment_data_from_pdfs.json'
with open(results_file, 'w') as f:
    json.dump(extraction_results, f, indent=2)

print(f"\nResults saved to: {results_file}\n")

# Summary statistics
companies_with_data = sum(1 for data in extraction_results.values()
                         if any(data['2023'] or data['2024']))

print(f"Companies with extraction data: {companies_with_data}/{len(COMPANY_NAMES)}")
print("\nSample data:")
for company in list(extraction_results.keys())[:5]:
    if company in extraction_results:
        print(f"\n{company}:")
        print(f"  2023: {extraction_results[company]['2023']}")
        print(f"  2024: {extraction_results[company]['2024']}")

EOF
