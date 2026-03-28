#!/usr/bin/env python3
"""
Extract financial data from all 40 company PDFs.
Saves results and generates statistics.
"""

from pathlib import Path
from pdf_parser import PDFStatementParser
import json
from datetime import datetime

def extract_all_pdfs():
    """Extract financial data from all PDFs in pdfs/ directory."""

    parser = PDFStatementParser()
    pdf_dir = Path('pdfs')

    pdfs = sorted(pdf_dir.glob('*.pdf'))
    total_pdfs = len(pdfs)

    print(f"Extracting financial data from {total_pdfs} PDFs...\n")

    results = {
        'extraction_timestamp': datetime.now().isoformat(),
        'total_pdfs': total_pdfs,
        'pdfs_processed': 0,
        'pdfs_successful': 0,
        'pdfs_failed': 0,
        'companies': {}
    }

    stats = {
        'balance_sheet_items': [],
        'income_statement_items': [],
        'cash_flow_items': [],
        'financial_notes_sections': [],
        'mda_subsections': [],
        'equation_valid_count': 0,
        'equation_near_balance_count': 0,
        'equation_out_of_balance_count': 0,
        'missing_components_count': 0,
        'pdfs_with_cash_flow': 0,
        'pdfs_with_mda': 0,
        'pdfs_with_segments': 0,
        'errors': []
    }

    for idx, pdf_file in enumerate(pdfs, 1):
        print(f"[{idx}/{total_pdfs}] Processing: {pdf_file.name[:50]}...", end=' ')

        try:
            result = parser.parse_pdf(str(pdf_file))

            if 'error' in result:
                print(f"ERROR: {result['error'][:50]}")
                stats['errors'].append({
                    'file': pdf_file.name,
                    'error': result['error']
                })
                results['pdfs_failed'] += 1
            else:
                # Extract company name from PDF filename if metadata is missing
                company_name = result['metadata']['company']
                year = result['metadata'].get('year', 2024)

                if not company_name or company_name == 'Unknown':
                    # Try to extract from filename (e.g., "Markel-Bermuda-Limited---2020" -> "Markel Bermuda Limited")
                    filename = pdf_file.name
                    # Remove timestamp prefix (e.g., "2021-07-26-14-13-15-")
                    parts = filename.split('-')
                    # Find where the company name starts (after the timestamp)
                    if len(parts) > 6:
                        company_part = '-'.join(parts[6:])
                        # Remove the year suffix and extension
                        company_part = company_part.split('---')[0].replace('.pdf', '')
                        company_name = company_part.replace('-', ' ')

                if not company_name or company_name == 'Unknown':
                    company_name = f"Unknown-{idx}"

                bs_count = len(result['balance_sheet'])
                is_count = len(result['income_statement'])
                cf_count = len(result.get('cash_flow', {}))
                fn_count = len(result.get('financial_notes', {}))
                mda_count = len(result.get('management_discussion_analysis', {}))
                seg_count = len(result.get('segments', {}))
                inv_count = len(result.get('investments', {}))

                # Track equation validation
                eq_validation = result.get('equation_validation', {})
                if eq_validation.get('equation_valid'):
                    stats['equation_valid_count'] += 1
                elif eq_validation.get('has_all_components'):
                    diff_pct = eq_validation.get('difference_pct', 100)
                    if diff_pct < 1:
                        stats['equation_near_balance_count'] += 1
                    else:
                        stats['equation_out_of_balance_count'] += 1
                else:
                    stats['missing_components_count'] += 1

                # Create unique key: company_name + year (to avoid overwrites)
                # Use company-year combo to handle multiple years per company
                unique_key = f"{company_name}_{year}"

                # Store company data with unique key
                results['companies'][unique_key] = {
                    'company_name': company_name,
                    'source_pdf': pdf_file.name,
                    'year': year,
                    'balance_sheet': result['balance_sheet'],
                    'income_statement': result['income_statement'],
                    'cash_flow': result.get('cash_flow', {}),
                    'management_discussion_analysis': result.get('management_discussion_analysis', {}),
                    'financial_notes': result['financial_notes'],
                    'segments': result.get('segments', {}),
                    'investments': result.get('investments', {}),
                    'ownership_structure': result['ownership_structure'],
                    'extraction_stats': result['extraction_stats'],
                    'equation_validation': eq_validation
                }

                stats['balance_sheet_items'].append(bs_count)
                stats['income_statement_items'].append(is_count)
                stats['cash_flow_items'].append(cf_count)
                stats['financial_notes_sections'].append(fn_count)
                stats['mda_subsections'].append(mda_count)

                if cf_count > 0:
                    stats['pdfs_with_cash_flow'] += 1
                if mda_count > 0:
                    stats['pdfs_with_mda'] += 1
                if seg_count > 0:
                    stats['pdfs_with_segments'] += 1

                # Show validation status
                val_status = 'OK' if eq_validation.get('equation_valid') else 'BAL'
                print(f"OK (BS: {bs_count}, IS: {is_count}, CF: {cf_count}, Notes: {fn_count}, MD&A: {mda_count}, Eq: {val_status})")
                results['pdfs_successful'] += 1

        except Exception as e:
            print(f"EXCEPTION: {str(e)[:50]}")
            stats['errors'].append({
                'file': pdf_file.name,
                'error': str(e)
            })
            results['pdfs_failed'] += 1

        results['pdfs_processed'] += 1

    # Calculate statistics
    if stats['balance_sheet_items']:
        stats['avg_balance_sheet_items'] = sum(stats['balance_sheet_items']) / len(stats['balance_sheet_items'])
        stats['min_balance_sheet_items'] = min(stats['balance_sheet_items'])
        stats['max_balance_sheet_items'] = max(stats['balance_sheet_items'])

    if stats['income_statement_items']:
        stats['avg_income_statement_items'] = sum(stats['income_statement_items']) / len(stats['income_statement_items'])
        stats['min_income_statement_items'] = min(stats['income_statement_items'])
        stats['max_income_statement_items'] = max(stats['income_statement_items'])

    if stats['cash_flow_items']:
        stats['avg_cash_flow_items'] = sum(stats['cash_flow_items']) / len(stats['cash_flow_items'])

    if stats['financial_notes_sections']:
        stats['avg_financial_notes_sections'] = sum(stats['financial_notes_sections']) / len(stats['financial_notes_sections'])

    if stats['mda_subsections']:
        stats['avg_mda_subsections'] = sum(stats['mda_subsections']) / len(stats['mda_subsections'])

    results['statistics'] = stats

    # Save results
    output_file = Path('extraction_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total PDFs: {results['pdfs_processed']}")
    print(f"Successful: {results['pdfs_successful']}")
    print(f"Failed: {results['pdfs_failed']}")
    print(f"\nBalance Sheet Items:")
    print(f"  Average: {stats.get('avg_balance_sheet_items', 0):.1f}")
    print(f"  Range: {stats.get('min_balance_sheet_items', 0)} - {stats.get('max_balance_sheet_items', 0)}")
    print(f"\nIncome Statement Items:")
    print(f"  Average: {stats.get('avg_income_statement_items', 0):.1f}")
    print(f"  Range: {stats.get('min_income_statement_items', 0)} - {stats.get('max_income_statement_items', 0)}")
    print(f"\nEquation Validation (Total Assets = Total Liabilities + Equity):")
    print(f"  Valid (< 0.1% difference): {stats['equation_valid_count']}")
    print(f"  Near balance (< 1% difference): {stats['equation_near_balance_count']}")
    print(f"  Out of balance (> 1% difference): {stats['equation_out_of_balance_count']}")
    print(f"  Missing components: {stats['missing_components_count']}")
    print(f"\nResults saved to: {output_file}")

    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:
            print(f"  - {error['file']}: {error['error'][:50]}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")

    return results

if __name__ == '__main__':
    extract_all_pdfs()
