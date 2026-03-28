#!/usr/bin/env python3
"""
Knowledge Base Validator
Validates that rebuilt KB matches PDF source data.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class KBValidator:
    """Validates knowledge base accuracy against extracted PDF data."""

    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.data_dir = self.repo_root / 'data'
        self.extracted_data_path = self.data_dir / 'extracted_pdf_data.json'
        self.kb_path = self.data_dir / 'knowledge_base.json'

    def load_extracted_data(self) -> Dict[str, Any]:
        """Load extracted PDF data."""
        if not self.extracted_data_path.exists():
            print(f"Error: Extracted data not found: {self.extracted_data_path}")
            return {}

        with open(self.extracted_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_kb(self) -> Dict[str, Any]:
        """Load knowledge base."""
        if not self.kb_path.exists():
            print(f"Error: Knowledge base not found: {self.kb_path}")
            return {}

        with open(self.kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def verify_line_item(
        self,
        company: str,
        year: int,
        metric: str,
        kb_value: float,
        pdf_value: float,
        tolerance: float = 0.01
    ) -> Tuple[bool, str]:
        """
        Compare KB value to extracted PDF value.

        tolerance: Acceptable difference as fraction (0.01 = 1%)
        """
        if pdf_value == 0:
            if kb_value == 0:
                return True, "Match (both zero)"
            else:
                return False, f"KB: {kb_value}, PDF: 0 (mismatch on zero)"

        difference = abs(kb_value - pdf_value) / pdf_value

        if difference <= tolerance:
            return True, f"Match (diff: {difference*100:.2f}%)"
        else:
            return False, f"MISMATCH: KB={kb_value:,}, PDF={pdf_value:,} (diff: {difference*100:.1f}%)"

    def validate_company_kb(self, company: str, year: int) -> Dict[str, Any]:
        """
        Validate KB entry for specific company and year.

        Returns:
            Validation report with findings
        """
        extracted = self.load_extracted_data()
        kb = self.load_kb()

        report = {
            'company': company,
            'year': year,
            'status': 'UNKNOWN',
            'findings': [],
            'mismatches': [],
            'coverage': {
                'balance_sheet': 0,
                'income_statement': 0
            }
        }

        # Find company data in extracted PDF data
        pdf_key = f"{company}_{year}"
        pdf_data = None

        for key, data in extracted.get('companies', {}).items():
            if company.lower() in key.lower() and str(year) in key:
                pdf_data = data
                pdf_key = key
                break

        if not pdf_data:
            report['status'] = 'NOT_FOUND'
            report['findings'].append(f"Company {company} {year} not found in extracted PDF data")
            return report

        # Find company in KB
        kb_company = None
        for kb_comp_name, kb_comp_data in kb.get('companies', {}).items():
            if company.lower() in kb_comp_name.lower():
                kb_company = kb_comp_data
                break

        if not kb_company:
            report['status'] = 'NOT_IN_KB'
            report['findings'].append(f"Company {company} not found in KB")
            return report

        # Validate period data
        if str(year) not in kb_company.get('periods', {}):
            report['status'] = 'YEAR_NOT_FOUND'
            report['findings'].append(f"Year {year} not found in KB for {company}")
            return report

        kb_period = kb_company['periods'][str(year)]
        pdf_bs = pdf_data.get('balance_sheet', {})
        pdf_is = pdf_data.get('income_statement', {})

        # Validate balance sheet items
        kb_bs = kb_period.get('balance_sheet', {})
        bs_checked = 0
        bs_matches = 0

        for metric, pdf_entry in pdf_bs.items():
            pdf_value = pdf_entry.get('value', 0)

            # Check if metric exists in KB
            if metric in kb_bs:
                kb_value = kb_bs[metric]
                if isinstance(kb_value, dict):
                    kb_value = kb_value.get('value', 0)

                bs_checked += 1
                is_match, msg = self.verify_line_item(company, year, metric, kb_value, pdf_value)

                if is_match:
                    bs_matches += 1
                    report['findings'].append(f"[OK] BS {metric}: {msg}")
                else:
                    report['findings'].append(f"[MISMATCH] BS {metric}: {msg}")
                    report['mismatches'].append({
                        'type': 'balance_sheet',
                        'metric': metric,
                        'kb_value': kb_value,
                        'pdf_value': pdf_value
                    })
            else:
                report['findings'].append(f"[WARN] BS {metric}: NOT IN KB")

        if bs_checked > 0:
            report['coverage']['balance_sheet'] = f"{bs_matches}/{bs_checked}"

        # Validate income statement items
        kb_is = kb_period.get('income_statement', {})
        is_checked = 0
        is_matches = 0

        for metric, pdf_entry in pdf_is.items():
            pdf_value = pdf_entry.get('value', 0)

            if metric in kb_is:
                kb_value = kb_is[metric]
                if isinstance(kb_value, dict):
                    kb_value = kb_value.get('value', 0)

                is_checked += 1
                is_match, msg = self.verify_line_item(company, year, metric, kb_value, pdf_value)

                if is_match:
                    is_matches += 1
                    report['findings'].append(f"[OK] IS {metric}: {msg}")
                else:
                    report['findings'].append(f"[MISMATCH] IS {metric}: {msg}")
                    report['mismatches'].append({
                        'type': 'income_statement',
                        'metric': metric,
                        'kb_value': kb_value,
                        'pdf_value': pdf_value
                    })
            else:
                report['findings'].append(f"[WARN] IS {metric}: NOT IN KB")

        if is_checked > 0:
            report['coverage']['income_statement'] = f"{is_matches}/{is_checked}"

        # Determine overall status
        total_mismatches = len(report['mismatches'])
        if total_mismatches == 0:
            report['status'] = 'VALID'
        elif total_mismatches < 3:
            report['status'] = 'MOSTLY_VALID'
        else:
            report['status'] = 'INVALID'

        return report

    def check_page_citations(self) -> Dict[str, Any]:
        """Verify all values have PDF page references."""
        kb = self.load_kb()

        report = {
            'total_companies': 0,
            'with_citations': 0,
            'without_citations': 0,
            'missing_companies': []
        }

        for company, data in kb.get('companies', {}).items():
            report['total_companies'] += 1

            periods = data.get('periods', {})
            has_all_citations = True

            for year, period_data in periods.items():
                bs = period_data.get('balance_sheet', {})
                is_stmt = period_data.get('income_statement', {})

                # Check BS items for page references
                for metric, item in bs.items():
                    if isinstance(item, dict) and 'page' not in item:
                        has_all_citations = False

                # Check IS items for page references
                for metric, item in is_stmt.items():
                    if isinstance(item, dict) and 'page' not in item:
                        has_all_citations = False

            if has_all_citations:
                report['with_citations'] += 1
            else:
                report['without_citations'] += 1
                report['missing_companies'].append(company)

        return report

    def generate_validation_report(self, company: str = None, year: int = None) -> str:
        """Generate validation report."""
        print("=" * 70)
        print("KNOWLEDGE BASE VALIDATION REPORT")
        print("=" * 70)

        if company and year:
            # Single company validation
            print(f"\nValidating: {company} ({year})")
            print("-" * 70)

            report = self.validate_company_kb(company, year)

            print(f"Status: {report['status']}")
            print(f"Balance Sheet Coverage: {report['coverage']['balance_sheet']}")
            print(f"Income Statement Coverage: {report['coverage']['income_statement']}")

            if report['findings']:
                print(f"\nFindings ({len(report['findings'])}):")
                for finding in report['findings'][:20]:  # Show first 20
                    print(f"  {finding}")

                if len(report['findings']) > 20:
                    print(f"  ... and {len(report['findings']) - 20} more")

            if report['mismatches']:
                print(f"\nMismatches ({len(report['mismatches'])}):")
                for mismatch in report['mismatches'][:10]:
                    print(f"  {mismatch['metric']}: KB={mismatch['kb_value']:,}, PDF={mismatch['pdf_value']:,}")

        else:
            # Global citation check
            print("\nChecking page citations across all companies...")
            print("-" * 70)

            citation_report = self.check_page_citations()

            print(f"Total companies: {citation_report['total_companies']}")
            print(f"With citations: {citation_report['with_citations']}")
            print(f"Without citations: {citation_report['without_citations']}")

            if citation_report['missing_companies']:
                print(f"\nCompanies missing citations:")
                for company in citation_report['missing_companies'][:10]:
                    print(f"  - {company}")

        print("\n" + "=" * 70)

    def run(self, company: str = None, year: int = None) -> bool:
        """Run validation."""
        try:
            self.generate_validation_report(company, year)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


def main():
    """Entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate Knowledge Base')
    parser.add_argument('--company', type=str, help='Company name to validate')
    parser.add_argument('--year', type=int, help='Year to validate')

    args = parser.parse_args()

    validator = KBValidator()
    success = validator.run(args.company, args.year)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
