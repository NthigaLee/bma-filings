"""
Extract financial data from PDFs for 30 companies (10 original + 20 new)
Generates structured data for Excel workbook creation
"""

import pdfplumber
import re
from pathlib import Path
from collections import defaultdict

# Define the 30 companies
COMPANIES = [
    # Original 10
    "Arch Reinsurance",
    "Ascot Bermuda",
    "Aspen Bermuda",
    "AXIS Specialty",
    "Chubb Tempest Reinsurance",
    "Everest Reinsurance Bermuda",
    "Hannover Re Bermuda",
    "Markel Bermuda",
    "Partner Reinsurance Company",
    "Renaissance Reinsurance",
    # New 20
    "Endurance Specialty Insurance",
    "XL Bermuda",
    "AXA XL Reinsurance",
    "Validus Reinsurance",
    "Somers Re",
    "Lancashire Insurance Company",
    "Hiscox Insurance Company Bermuda",
    "Canopius Reinsurance",
    "Conduit Reinsurance",
    "Fidelis Insurance Bermuda",
    "Fortitude Reinsurance Company",
    "Group Ark Insurance",
    "Hamilton Re",
    "Harrington Re",
    "Liberty Specialty Markets Bermuda",
    "MS Amlin AG",
    "Premia Reinsurance",
    "Starr Insurance & Reinsurance",
    "Vantage Risk",
    "SiriusPoint Bermuda Insurance"
]

# Map company names to PDF file patterns
PDF_PATTERNS = {
    "Arch Reinsurance": "Arch-Reinsurance-Ltd",
    "Ascot Bermuda": "Ascot-Bermuda-Limited",
    "Aspen Bermuda": "Aspen-Bermuda-Limited",
    "AXIS Specialty": "Axis-Specialty",
    "Chubb Tempest Reinsurance": "Chubb-Tempest-Reinsurance-Ltd",
    "Everest Reinsurance Bermuda": "Everest-Reinsurance-Bermuda-Ltd",
    "Hannover Re Bermuda": "Hannover-Re-Bermuda-Ltd",
    "Markel Bermuda": "Markel-Bermuda-Limited",
    "Partner Reinsurance Company": "Partner-Reinsurance-Company-Ltd",
    "Renaissance Reinsurance": "Renaissance-Reinsurance-Ltd",
    "Endurance Specialty Insurance": "Endurance-Specialty-Insurance-Ltd",
    "XL Bermuda": "XL-Bermuda-Ltd",
    "AXA XL Reinsurance": "AXA-XL-Reinsurance-Ltd",
    "Validus Reinsurance": "Validus-Reinsurance-Ltd",
    "Somers Re": "Somers-Re-Ltd",
    "Lancashire Insurance Company": "Lancashire-Insurance-Company-Limited",
    "Hiscox Insurance Company Bermuda": "Hiscox-Insurance-Company-Bermuda-Limited",
    "Canopius Reinsurance": "Canopius-Reinsurance-Limited",
    "Conduit Reinsurance": "Conduit-Reinsurance-Limited",
    "Fidelis Insurance Bermuda": "Fidelis-Insurance-Bermuda-Limited",
    "Fortitude Reinsurance Company": "Fortitude-Reinsurance-Company-Ltd",
    "Group Ark Insurance": "Group-Ark-Insurance-Limited",
    "Hamilton Re": "Hamilton-Re-Ltd",
    "Harrington Re": "Harrington-Re-Ltd",
    "Liberty Specialty Markets Bermuda": "Liberty-Specialty-Markets-Bermuda-Limited",
    "MS Amlin AG": "MS-Amlin-AG",
    "Premia Reinsurance": "Premia-Reinsurance-Ltd",
    "Starr Insurance & Reinsurance": "Starr-Insurance--Reinsurance-Limited",
    "Vantage Risk": "Vantage-Risk-Ltd",
    "SiriusPoint Bermuda Insurance": "Siriuspoint-Bermuda-Insurance-Company-Ltd"
}

# Financial line items to extract
BALANCE_SHEET_ITEMS = [
    "Total Investments",
    "Cash and Cash Equivalents",
    "Total Assets",
    "Loss Reserves",
    "Unearned Premiums",
    "Total Liabilities",
    "Total Equity"
]

INCOME_STATEMENT_ITEMS = [
    "Gross Premiums Written",
    "Net Premiums Earned",
    "Total Revenues",
    "Total Expenses",
    "Net Income"
]

LOSS_ITEMS = [
    "Losses and loss adjustment",
    "Net incurred losses",
    "Claims and claim adjustment"
]

def find_pdf_files(company_name, year):
    """Find PDF files for a company and year"""
    pdf_dir = Path("C:/Users/nthig/.claude/projects/bma-filings/pdfs")
    pattern = PDF_PATTERNS.get(company_name, "")

    if not pattern:
        return None

    # Search for files matching the pattern and year
    for pdf_file in pdf_dir.glob("*"):
        if pattern in pdf_file.name and f"{year}-Financial-Statement" in pdf_file.name:
            return str(pdf_file)

    return None

def extract_number_from_text(text):
    """Extract numerical value from text"""
    if not text:
        return None

    # Remove common separators and convert to number
    text = str(text).strip()

    # Remove parentheses (negative values)
    is_negative = "(" in text and ")" in text

    # Extract digits and decimal point
    numbers = re.findall(r'[\d.]+', text.replace(',', ''))

    if numbers:
        try:
            value = float(numbers[0])
            if is_negative:
                value = -value
            return value
        except:
            return None

    return None

def extract_from_pdf(pdf_path, company_name):
    """Extract financial data from a PDF file"""
    print(f"Extracting from {Path(pdf_path).name}...")

    data = {
        "balance_sheet": {},
        "income_statement": {},
        "losses": None
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""

            # Search for financial line items
            for item in BALANCE_SHEET_ITEMS:
                # Search for the item in text and extract number
                pattern = rf"{item}[\s\S]*?[\$]?\s*([\d,\.]+(?:\s*\([0-9,\.]+\))?|\([0-9,\.]+\))"
                matches = re.finditer(pattern, full_text, re.IGNORECASE)

                for match in matches:
                    value_text = match.group(1) if match.lastindex >= 1 else ""
                    value = extract_number_from_text(value_text)
                    if value is not None and value != 0:
                        data["balance_sheet"][item] = value
                        break

            # Search for income statement items
            for item in INCOME_STATEMENT_ITEMS:
                pattern = rf"{item}[\s\S]*?[\$]?\s*([\d,\.]+(?:\s*\([0-9,\.]+\))?|\([0-9,\.]+\))"
                matches = re.finditer(pattern, full_text, re.IGNORECASE)

                for match in matches:
                    value_text = match.group(1) if match.lastindex >= 1 else ""
                    value = extract_number_from_text(value_text)
                    if value is not None and value != 0:
                        data["income_statement"][item] = value
                        break

            # Search for loss data
            for loss_item in LOSS_ITEMS:
                pattern = rf"{loss_item}[\s\S]*?[\$]?\s*([\d,\.]+(?:\s*\([0-9,\.]+\))?|\([0-9,\.]+\))"
                matches = re.finditer(pattern, full_text, re.IGNORECASE)

                for match in matches:
                    value_text = match.group(1) if match.lastindex >= 1 else ""
                    value = extract_number_from_text(value_text)
                    if value is not None and value != 0:
                        data["losses"] = value
                        break

                if data["losses"]:
                    break

    except Exception as e:
        print(f"Error processing {company_name}: {str(e)}")

    return data

def extract_all_companies():
    """Extract data for all 30 companies"""
    all_data = {}

    for year in [2024, 2023]:
        print(f"\n{'='*60}")
        print(f"Extracting {year} Data")
        print(f"{'='*60}")

        year_data = {}

        for company in COMPANIES:
            print(f"\n{company} ({year})...")
            pdf_path = find_pdf_files(company, year)

            if pdf_path:
                data = extract_from_pdf(pdf_path, company)
                year_data[company] = data
                print(f"  [OK] Extracted balance sheet, income statement, and losses")
            else:
                print(f"  [NOT FOUND] PDF not found")
                year_data[company] = {
                    "balance_sheet": {},
                    "income_statement": {},
                    "losses": None
                }

        all_data[year] = year_data

    return all_data

def print_summary(all_data):
    """Print extraction summary"""
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}\n")

    for year in sorted(all_data.keys(), reverse=True):
        print(f"\n{year} Data Summary:")
        print("-" * 60)

        for company, data in all_data[year].items():
            bs_count = len(data["balance_sheet"])
            is_count = len(data["income_statement"])
            losses = "Yes" if data["losses"] else "No"

            print(f"{company:45} | BS: {bs_count:2d} | IS: {is_count:2d} | Loss: {losses}")

if __name__ == "__main__":
    print("Starting financial data extraction for 30 companies...")
    all_data = extract_all_companies()
    print_summary(all_data)

    # Save extracted data for reference
    import json
    with open("extracted_30_companies.json", "w") as f:
        # Convert to serializable format
        serializable_data = {}
        for year, companies in all_data.items():
            serializable_data[year] = {}
            for company, data in companies.items():
                serializable_data[year][company] = {
                    "balance_sheet": data["balance_sheet"],
                    "income_statement": data["income_statement"],
                    "losses": data["losses"]
                }
        json.dump(serializable_data, f, indent=2)

    print("\n✓ Extracted data saved to 'extracted_30_companies.json'")
