#!/usr/bin/env python3
"""
Extract losses and LAE directly from PDF financial statements
"""
import pdfplumber
from pathlib import Path

# PDF file paths
PDF_DIR = Path("pdfs")

COMPANIES = [
    ("Arch", "Arch_Reinsurance_10-K_2024.pdf"),
    ("Ascot", "Ascot_Bermuda_10-K_2024.pdf"),
    ("Aspen", "Aspen_Bermuda_10-K_2024.pdf"),
    ("AXIS", "AXIS_Specialty_10-K_2024.pdf"),
    ("Chubb", "Chubb_Tempest_10-K_2024.pdf"),
    ("Everest", "Everest_Reinsurance_10-K_2024.pdf"),
    ("Hannover", "Hannover_Re_Bermuda_10-K_2024.pdf"),
    ("Markel", "Markel_Bermuda_10-K_2024.pdf"),
    ("Partner", "Partner_Reinsurance_10-K_2024.pdf"),
    ("Renaissance", "Renaissance_Reinsurance_10-K_2024.pdf"),
]

def extract_losses_from_pdf(pdf_path, company_name):
    """
    Extract losses and LAE from PDF income statement
    Looking for: "Losses and loss adjustment expenses" or similar
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\n{company_name}:")
            print(f"  PDF: {pdf_path.name}")
            print(f"  Pages: {len(pdf.pages)}")

            # Search through all pages for loss-related text
            found_losses = False

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    # Look for loss-related lines
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        line_upper = line.upper()
                        if 'LOSS' in line_upper and ('ADJUSTMENT' in line_upper or 'LAE' in line_upper):
                            print(f"  Page {page_num}: {line.strip()}")
                            # Try to get the next few lines for context
                            if i + 1 < len(lines):
                                print(f"    Next: {lines[i+1].strip()}")
                            found_losses = True

            if not found_losses:
                print(f"  ⚠ No loss data found in PDF")

    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("=" * 70)
    print("LOSS DATA EXTRACTION FROM PDF FINANCIAL STATEMENTS")
    print("=" * 70)

    for company_short, pdf_file in COMPANIES:
        pdf_path = PDF_DIR / pdf_file
        if pdf_path.exists():
            extract_losses_from_pdf(pdf_path, company_short)
        else:
            print(f"\n{company_short}:")
            print(f"  PDF NOT FOUND: {pdf_path}")

if __name__ == "__main__":
    main()
