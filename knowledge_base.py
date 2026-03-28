#!/usr/bin/env python3
"""
Company Knowledge Base Builder
Indexes all company financial data, statements, ownership, and descriptions
for local caching and faster bot operations.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

REPO_ROOT = Path(__file__).parent
KB_PATH = REPO_ROOT / 'data' / 'knowledge_base.json'
EXTRACTED_PDF_PATH = REPO_ROOT / 'data' / 'extracted_pdf_data.json'
DASHBOARD_PATH = REPO_ROOT / 'dashboard_data.json'
COMPANY_SUMMARIES_DIR = REPO_ROOT / 'data' / 'company_summaries'


def load_extracted_pdf_data() -> Dict[str, Any]:
    """Load extracted PDF data from extracted_pdf_data.json (PRIMARY SOURCE)."""
    try:
        with open(EXTRACTED_PDF_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading extracted PDF data: {e}")
        print("Falling back to dashboard data...")
        return load_dashboard_data()


def load_dashboard_data() -> Dict[str, Any]:
    """Load dashboard data from dashboard_data.json (FALLBACK)."""
    try:
        with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        return {}


def extract_company_info(extracted_data: Dict) -> Dict[str, Dict]:
    """Extract company information from extracted PDF data or dashboard data."""
    companies = {}

    # Check if this is extracted PDF data (new format)
    if 'companies' in extracted_data:
        # New format from extract_all_pdfs.py
        for key, company_data in extracted_data.get('companies', {}).items():
            # Get company name - prefer explicit company_name field, else extract from metadata
            company_name = company_data.get('company_name')

            if not company_name:
                metadata = company_data.get('metadata', {})
                company_name = metadata.get('company', 'Unknown')

                # Extract from source PDF filename if still missing
                if company_name == 'Unknown' or not company_name or company_name.isdigit():
                    source_pdf = company_data.get('source_pdf', '')
                    if source_pdf:
                        # Parse filename: YYYY-MM-DD-HH-MM-SS-CompanyName---Year-...
                        parts = source_pdf.split('-')
                        if len(parts) > 6:
                            company_part = '-'.join(parts[6:])
                            company_part = company_part.split('---')[0].replace('.pdf', '')
                            company_name = company_part.replace('-', ' ').strip()

                    # If still not a good name, fall back to key
                    if not company_name or company_name.isdigit():
                        company_name = key.rsplit('_', 1)[0] if '_' in key else key

            year = company_data.get('year', 2024)

            if company_name not in companies:
                companies[company_name] = {}

            companies[company_name][str(year)] = {
                'balance_sheet': company_data.get('balance_sheet', {}),
                'income_statement': company_data.get('income_statement', {}),
                'cash_flow': company_data.get('cash_flow', {}),
                'management_discussion_analysis': company_data.get('management_discussion_analysis', {}),
                'financial_notes': company_data.get('financial_notes', {}),
                'segments': company_data.get('segments', {}),
                'investments': company_data.get('investments', {}),
                'ratios': {},
                'source_pdf': company_data.get('source_pdf', ''),
                'statement_pages': company_data.get('statement_pages', {})
            }

    else:
        # Fallback to old dashboard data format
        data = extracted_data.get('data', {})

        for year, year_data in data.items():
            balance_sheet = year_data.get('balance_sheet', {})
            income_statement = year_data.get('income_statement', {})
            ratios = year_data.get('ratios', {})

            if balance_sheet:
                companies_in_year = list(balance_sheet.values())[0].keys() if balance_sheet.values() else []
            elif income_statement:
                companies_in_year = list(income_statement.values())[0].keys() if income_statement.values() else []
            else:
                companies_in_year = []

            for company in companies_in_year:
                if company not in companies:
                    companies[company] = {}

                companies[company][year] = {
                    'balance_sheet': {},
                    'income_statement': {},
                    'ratios': {}
                }

                for metric, values in balance_sheet.items():
                    if isinstance(values, dict) and company in values:
                        companies[company][year]['balance_sheet'][metric] = values[company]

                for metric, values in income_statement.items():
                    if isinstance(values, dict) and company in values:
                        companies[company][year]['income_statement'][metric] = values[company]

                for metric, values in ratios.items():
                    if isinstance(values, dict) and company in values:
                        companies[company][year]['ratios'][metric] = values[company]

    return companies


def build_company_summary(company: str, financial_data: Dict) -> Dict[str, Any]:
    """Build a comprehensive summary for a company."""
    summary = {
        'name': company,
        'description': generate_company_description(company, financial_data),
        'periods': {},
        'ownership': extract_ownership_structure(company, financial_data),
        'key_metrics': extract_key_metrics(company, financial_data),
        'trends': calculate_trends(company, financial_data),
        'last_updated': datetime.now(timezone.utc).isoformat()
    }

    # Add financial data for each period
    for year, year_data in financial_data.items():
        summary['periods'][year] = {
            'balance_sheet': year_data.get('balance_sheet', {}),
            'income_statement': year_data.get('income_statement', {}),
            'cash_flow': year_data.get('cash_flow', {}),
            'management_discussion_analysis': year_data.get('management_discussion_analysis', {}),
            'financial_notes': year_data.get('financial_notes', {}),
            'segments': year_data.get('segments', {}),
            'investments': year_data.get('investments', {}),
            'ratios': year_data.get('ratios', {}),
            'notes': extract_financial_notes(company, year, year_data)
        }

    return summary


def generate_company_description(company: str, financial_data: Dict) -> str:
    """Generate a description based on company type and financial profile."""
    descriptions = {
        'Arch Reinsurance': 'Global reinsurance company specializing in catastrophe and specialty reinsurance.',
        'Aspen Bermuda': 'Bermuda-based insurance and reinsurance company with global operations.',
        'AXIS Specialty': 'Specialty insurance and reinsurance company providing coverages for complex risks.',
        'Markel Bermuda': 'Insurance company offering property, casualty, and specialty insurance products.',
        'XL Bermuda': 'Insurance and reinsurance company focusing on specialty and catastrophe risk.',
    }

    # Return specific description if available, otherwise generate generic one
    return descriptions.get(company, f"{company} is an insurance/reinsurance company providing coverage for various risk categories.")


def extract_ownership_structure(company: str, financial_data: Dict) -> Dict[str, Any]:
    """Extract ownership structure information."""
    # This would typically come from company snapshots or additional data
    # For now, return a structure that can be populated
    return {
        'primary_shareholders': [],
        'share_structure': {},
        'ownership_type': 'Public' if 'Arch' in company or 'Aspen' in company else 'Private',
        'domicile': 'Bermuda' if 'Bermuda' in company else 'USA',
        'regulatory_body': 'BMA' if 'Bermuda' in company else 'State Insurance Commissioner'
    }


def extract_key_metrics(company: str, financial_data: Dict) -> Dict[str, float]:
    """Extract the most important financial metrics across periods."""
    metrics = {}

    # Helper function to extract numeric values
    def get_value(item):
        if isinstance(item, dict):
            return item.get('value', 0)
        return item

    # Get latest year data
    if financial_data:
        latest_year = max(financial_data.keys())
        latest = financial_data[latest_year]

        # Key metrics from ratios
        if latest.get('ratios'):
            metrics['combined_ratio'] = get_value(latest['ratios'].get('Combined Ratio', 0))
            metrics['roe'] = get_value(latest['ratios'].get('ROE', 0))
            metrics['equity_ratio'] = get_value(latest['ratios'].get('Equity Ratio', 0))

        # Key metrics from balance sheet
        if latest.get('balance_sheet'):
            metrics['total_assets'] = get_value(latest['balance_sheet'].get('Total Assets', 0))
            metrics['total_equity'] = get_value(latest['balance_sheet'].get('Total Shareholders Equity',
                                                 latest['balance_sheet'].get('Total Equity', 0)))

        # Key metrics from income statement
        if latest.get('income_statement'):
            metrics['net_income'] = get_value(latest['income_statement'].get('Net Income', 0))
            metrics['premiums'] = get_value(latest['income_statement'].get('Premiums',
                                           latest['income_statement'].get('Gross Premiums Written', 0)))

    return metrics


def calculate_trends(company: str, financial_data: Dict) -> Dict[str, Any]:
    """Calculate year-over-year trends."""
    trends = {
        'premium_growth': 0,
        'asset_growth': 0,
        'equity_growth': 0,
        'ratio_changes': {}
    }

    # Helper function to extract numeric values
    def get_value(item):
        if isinstance(item, dict):
            return item.get('value', 0)
        return item

    years = sorted(financial_data.keys())

    if len(years) >= 2:
        prev_year = years[-2]
        curr_year = years[-1]

        prev = financial_data[prev_year]
        curr = financial_data[curr_year]

        # Premium growth
        prev_premium = get_value(prev.get('income_statement', {}).get('Premiums',
                                prev.get('income_statement', {}).get('Gross Premiums Written', 0)))
        curr_premium = get_value(curr.get('income_statement', {}).get('Premiums',
                                curr.get('income_statement', {}).get('Gross Premiums Written', 0)))
        if prev_premium > 0:
            trends['premium_growth'] = ((curr_premium - prev_premium) / prev_premium) * 100

        # Asset growth
        prev_assets = get_value(prev.get('balance_sheet', {}).get('Total Assets', 0))
        curr_assets = get_value(curr.get('balance_sheet', {}).get('Total Assets', 0))
        if prev_assets > 0:
            trends['asset_growth'] = ((curr_assets - prev_assets) / prev_assets) * 100

        # Equity growth
        prev_equity = get_value(prev.get('balance_sheet', {}).get('Total Shareholders Equity',
                               prev.get('balance_sheet', {}).get('Total Equity', 0)))
        curr_equity = get_value(curr.get('balance_sheet', {}).get('Total Shareholders Equity',
                               curr.get('balance_sheet', {}).get('Total Equity', 0)))
        if prev_equity > 0:
            trends['equity_growth'] = ((curr_equity - prev_equity) / prev_equity) * 100

    return trends


def extract_financial_notes(company: str, year: str, year_data: Dict) -> Dict[str, str]:
    """Extract or generate financial notes for a period."""
    notes = {
        'balance_sheet_notes': generate_bs_notes(company, year, year_data),
        'income_statement_notes': generate_is_notes(company, year, year_data),
        'risk_factors': generate_risk_notes(company, year, year_data),
        'accounting_methods': 'GAAP-based accounting standards applied consistently year-over-year.'
    }
    return notes


def generate_bs_notes(company: str, year: str, year_data: Dict) -> str:
    """Generate balance sheet notes."""
    bs = year_data.get('balance_sheet', {})

    # Extract numeric value from balance sheet item (handles both new and old formats)
    total_assets_item = bs.get('Total Assets', 0)
    total_assets = total_assets_item.get('value', total_assets_item) if isinstance(total_assets_item, dict) else total_assets_item

    total_equity_item = bs.get('Total Shareholders Equity', bs.get('Total Equity', 0))
    total_equity = total_equity_item.get('value', total_equity_item) if isinstance(total_equity_item, dict) else total_equity_item

    if total_assets > 0:
        equity_ratio = (total_equity / total_assets) * 100
        return f"Balance sheet shows total assets of {total_assets:,.0f}. Equity ratio of {equity_ratio:.1f}% indicates {'strong' if equity_ratio > 25 else 'moderate' if equity_ratio > 15 else 'lower'} solvency position."
    return "Balance sheet data reflects period-end valuations."


def generate_is_notes(company: str, year: str, year_data: Dict) -> str:
    """Generate income statement notes."""
    inc = year_data.get('income_statement', {})

    # Extract numeric values (handles both new and old formats)
    premiums_item = inc.get('Premiums', inc.get('Gross Premiums Written', 0))
    premiums = premiums_item.get('value', premiums_item) if isinstance(premiums_item, dict) else premiums_item

    net_income_item = inc.get('Net Income', 0)
    net_income = net_income_item.get('value', net_income_item) if isinstance(net_income_item, dict) else net_income_item

    if premiums > 0:
        profit_margin = (net_income / premiums) * 100
        return f"Operating results show premiums of {premiums:,.0f} with net income of {net_income:,.0f}. Profit margin of {profit_margin:.1f}%."
    return "Income statement reflects underwriting and investment results for the period."


def generate_risk_notes(company: str, year: str, year_data: Dict) -> str:
    """Generate risk factor notes."""
    ratios = year_data.get('ratios', {})

    # Helper function to extract numeric values
    def get_value(item):
        if isinstance(item, dict):
            return item.get('value', 0)
        return item

    combined_ratio = get_value(ratios.get('Combined Ratio', 100))
    equity_ratio = get_value(ratios.get('Equity Ratio', 0))

    risk_factors = []

    if combined_ratio > 105:
        risk_factors.append("Combined ratio above 105% indicates underwriting losses")
    if combined_ratio > 110:
        risk_factors.append("Elevated combined ratio suggests operational stress")

    if equity_ratio < 0.20 and equity_ratio > 0:
        risk_factors.append("Lower equity ratio may limit capital capacity")

    if not risk_factors:
        risk_factors.append("Key risk metrics within acceptable ranges for the period")

    return "; ".join(risk_factors) + "."


def build_knowledge_base() -> Dict[str, Any]:
    """Build complete knowledge base from extracted PDF data (or dashboard fallback)."""
    print("[1] Loading extracted PDF data...")
    extracted_data = load_extracted_pdf_data()

    print("[2] Extracting company information...")
    companies_data = extract_company_info(extracted_data)

    print("[3] Building company-year entries...")

    # Determine data source
    data_source = 'extracted_pdf_data.json' if Path(EXTRACTED_PDF_PATH).exists() else 'dashboard_data.json'

    kb = {
        'metadata': {
            'created': datetime.now(timezone.utc).isoformat(),
            'version': '2.0',
            'total_companies': len(companies_data),
            'data_sources': [data_source],
            'extraction_method': 'PDF extraction with page citations' if data_source == 'extracted_pdf_data.json' else 'Dashboard data'
        },
        'companies': {}
    }

    # Create separate entries for each company-year combination
    entry_count = 0
    for company, financial_data in companies_data.items():
        # financial_data is {year: {balance_sheet, income_statement, ...}}
        for year, year_data in financial_data.items():
            # Create entry key: "Company Name YYYY"
            entry_key = f"{company} {year}"
            print(f"  - {entry_key}")

            # Build summary for this specific company-year
            kb['companies'][entry_key] = {
                'name': company,
                'year': year,
                'balance_sheet': year_data.get('balance_sheet', {}),
                'income_statement': year_data.get('income_statement', {}),
                'cash_flow': year_data.get('cash_flow', {}),
                'management_discussion_analysis': year_data.get('management_discussion_analysis', {}),
                'financial_notes': year_data.get('financial_notes', {}),
                'segments': year_data.get('segments', {}),
                'investments': year_data.get('investments', {}),
                'ratios': year_data.get('ratios', {}),
                'source_pdf': year_data.get('source_pdf', ''),
                'statement_pages': year_data.get('statement_pages', {}),
                'extraction_date': datetime.now(timezone.utc).isoformat()
            }
            entry_count += 1

    print(f"\n[4] Knowledge base built with {len(companies_data)} companies ({entry_count} company-year entries)")
    return kb


def save_knowledge_base(kb: Dict[str, Any]) -> None:
    """Save knowledge base to file."""
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, default=str)
    print(f"[5] Saved to: {KB_PATH}")


def save_individual_summaries(kb: Dict[str, Any]) -> None:
    """Save individual company-year summaries for quick access."""
    COMPANY_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    for entry_key, summary in kb.get('companies', {}).items():
        # Create filename from company-year key
        filename = entry_key.lower().replace(' ', '_').replace('.', '') + '.json'
        filepath = COMPANY_SUMMARIES_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)

    print(f"[6] Saved {len(kb.get('companies', {}))} company-year summaries to: {COMPANY_SUMMARIES_DIR}")


def load_knowledge_base() -> Dict[str, Any]:
    """Load existing knowledge base from file."""
    if KB_PATH.exists():
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_company_kb(company: str) -> Optional[Dict[str, Any]]:
    """Get knowledge base entry for a specific company."""
    kb = load_knowledge_base()
    return kb.get('companies', {}).get(company)


def search_kb(query: str, field: str = 'name') -> List[str]:
    """Search knowledge base for companies matching criteria."""
    kb = load_knowledge_base()
    results = []

    query_lower = query.lower()

    for company, data in kb.get('companies', {}).items():
        if field == 'name' and query_lower in company.lower():
            results.append(company)
        elif field == 'description' and query_lower in data.get('description', '').lower():
            results.append(company)
        elif field == 'ownership' and query_lower in str(data.get('ownership', '')).lower():
            results.append(company)

    return results


def get_kb_summary() -> Dict[str, Any]:
    """Get summary statistics about the knowledge base."""
    kb = load_knowledge_base()

    summary = {
        'total_companies': len(kb.get('companies', {})),
        'last_updated': kb.get('metadata', {}).get('created'),
        'companies_list': list(kb.get('companies', {}).keys())
    }

    return summary


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'build':
            kb = build_knowledge_base()
            save_knowledge_base(kb)
            save_individual_summaries(kb)
            print("\n[SUCCESS] Knowledge base built and saved")

        elif command == 'search':
            if len(sys.argv) > 2:
                query = sys.argv[2]
                results = search_kb(query)
                print(f"\nSearch results for '{query}':")
                for company in results:
                    print(f"  - {company}")
            else:
                print("Usage: python knowledge_base.py search <query>")

        elif command == 'info':
            summary = get_kb_summary()
            print("\n=== Knowledge Base Summary ===")
            print(f"Total Companies: {summary['total_companies']}")
            print(f"Last Updated: {summary['last_updated']}")
            print(f"\nCompanies:")
            for company in summary['companies_list']:
                print(f"  - {company}")

        else:
            print(f"Unknown command: {command}")

    else:
        # Default: build KB
        kb = build_knowledge_base()
        save_knowledge_base(kb)
        save_individual_summaries(kb)
        print("\n[SUCCESS] Knowledge base built successfully")
