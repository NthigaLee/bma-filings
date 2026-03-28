#!/usr/bin/env python3
"""
PDF Extractor CLI
Orchestrates extraction from all 40 company PDFs and builds comprehensive dataset.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from pdf_parser import PDFStatementParser


class PDFExtractor:
    """Orchestrates PDF extraction for all companies."""

    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.pdf_dir = self.repo_root / 'pdfs'
        self.data_dir = self.repo_root / 'data'
        self.extracted_data_path = self.data_dir / 'extracted_pdf_data.json'
        self.parser = PDFStatementParser()

    def discover_pdf_files(self) -> List[Path]:
        """Find all PDF files in pdfs directory."""
        if not self.pdf_dir.exists():
            print(f"Error: PDF directory not found: {self.pdf_dir}")
            return []

        pdfs = list(self.pdf_dir.glob('*.pdf'))
        print(f"Found {len(pdfs)} PDF files")
        return sorted(pdfs)

    def extract_all_companies(self) -> Dict[str, Any]:
        """
        Extract financial data from all PDF files.

        Returns:
            Dictionary mapping company-year keys to extracted data
        """
        pdfs = self.discover_pdf_files()

        if not pdfs:
            print("No PDFs found to extract")
            return {}

        extracted_data = {
            'metadata': {
                'extraction_date': __import__('datetime').datetime.now(
                    __import__('datetime').timezone.utc
                ).isoformat(),
                'total_files': len(pdfs),
                'successful': 0,
                'failed': 0,
                'parser': 'pdf_parser.py v1.0'
            },
            'companies': {}
        }

        print(f"\nExtracting from {len(pdfs)} PDF files...")
        print("=" * 60)

        for i, pdf_path in enumerate(pdfs, 1):
            print(f"\n[{i}/{len(pdfs)}] Processing: {pdf_path.name}")

            try:
                # Parse the PDF
                result = self.parser.parse_pdf(str(pdf_path))

                if 'error' in result:
                    print(f"  [FAIL] Error: {result['error']}")
                    extracted_data['metadata']['failed'] += 1
                    continue

                # Extract key info
                company = result['metadata']['company']
                year = result['metadata']['year']

                if not company or company == 'Unknown':
                    print(f"  ⚠ Warning: Could not identify company name")
                    company = pdf_path.stem

                if not year or year < 2000:
                    print(f"  ⚠ Warning: Could not identify year, using 2024")
                    year = 2024

                key = f"{company}_{year}"

                # Store extracted data
                extracted_data['companies'][key] = {
                    'metadata': result['metadata'],
                    'balance_sheet': result['balance_sheet'],
                    'income_statement': result['income_statement'],
                    'financial_notes': result['financial_notes'],
                    'ownership_structure': result['ownership_structure'],
                    'statement_pages': result['statement_pages'],
                    'source_pdf': result['source_pdf'],
                    'extraction_date': result['extraction_date']
                }

                # Print progress
                bs_count = len(result['balance_sheet'])
                is_count = len(result['income_statement'])
                print(f"  [OK] {company} ({year})")
                print(f"       - Balance sheet: {bs_count} items")
                print(f"       - Income statement: {is_count} items")
                print(f"       - Notes: {len(result['financial_notes'])} sections")

                extracted_data['metadata']['successful'] += 1

            except Exception as e:
                print(f"  [ERROR] Exception: {str(e)}")
                extracted_data['metadata']['failed'] += 1

        print("\n" + "=" * 60)
        print(f"Extraction complete:")
        print(f"  - Successful: {extracted_data['metadata']['successful']}")
        print(f"  - Failed: {extracted_data['metadata']['failed']}")
        print(f"  - Total companies: {len(extracted_data['companies'])}")

        return extracted_data

    def save_extracted_data(self, extracted_data: Dict[str, Any]) -> bool:
        """Save extracted data to JSON file."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)

            with open(self.extracted_data_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, default=str)

            file_size = self.extracted_data_path.stat().st_size / 1024
            print(f"\n[OK] Saved to: {self.extracted_data_path}")
            print(f"     File size: {file_size:.1f} KB")

            return True
        except Exception as e:
            print(f"\n[ERROR] Error saving extracted data: {e}")
            return False

    def validate_extraction_coverage(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that extraction covers expected data.

        Returns:
            Dictionary with coverage statistics
        """
        stats = {
            'total_companies': len(extracted_data['companies']),
            'with_balance_sheet': 0,
            'with_income_statement': 0,
            'with_notes': 0,
            'with_ownership': 0,
            'avg_bs_items': 0,
            'avg_is_items': 0,
            'missing_companies': []
        }

        total_bs_items = 0
        total_is_items = 0

        for key, data in extracted_data['companies'].items():
            if data['balance_sheet']:
                stats['with_balance_sheet'] += 1
                total_bs_items += len(data['balance_sheet'])

            if data['income_statement']:
                stats['with_income_statement'] += 1
                total_is_items += len(data['income_statement'])

            if data['financial_notes']:
                stats['with_notes'] += 1

            if data['ownership_structure'].get('ownership_type') != 'Unknown':
                stats['with_ownership'] += 1

        if stats['with_balance_sheet'] > 0:
            stats['avg_bs_items'] = total_bs_items / stats['with_balance_sheet']

        if stats['with_income_statement'] > 0:
            stats['avg_is_items'] = total_is_items / stats['with_income_statement']

        print(f"\nCoverage Analysis:")
        print(f"  Total companies: {stats['total_companies']}")
        print(f"  With balance sheet: {stats['with_balance_sheet']}/{stats['total_companies']}")
        print(f"  With income statement: {stats['with_income_statement']}/{stats['total_companies']}")
        print(f"  With financial notes: {stats['with_notes']}/{stats['total_companies']}")
        print(f"  With ownership info: {stats['with_ownership']}/{stats['total_companies']}")
        print(f"  Avg BS items per company: {stats['avg_bs_items']:.1f}")
        print(f"  Avg IS items per company: {stats['avg_is_items']:.1f}")

        return stats

    def run(self) -> bool:
        """
        Run complete extraction process.

        Steps:
        1. Discover PDF files
        2. Extract from all PDFs
        3. Validate coverage
        4. Save to JSON
        """
        print("BMA Filings - PDF Extraction Tool")
        print("=" * 60)

        # Extract all PDFs
        extracted_data = self.extract_all_companies()

        if not extracted_data['companies']:
            print("No data extracted")
            return False

        # Validate coverage
        self.validate_extraction_coverage(extracted_data)

        # Save results
        success = self.save_extracted_data(extracted_data)

        if success:
            print("\n[OK] Extraction complete and saved successfully")
            return True
        else:
            print("\n[FAIL] Extraction failed to save")
            return False


def main():
    """Entry point for CLI."""
    extractor = PDFExtractor()
    success = extractor.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
