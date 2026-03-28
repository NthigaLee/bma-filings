#!/usr/bin/env python3
"""
Omniscient Bot CLI - Phase 5
Direct CLI access to bot intelligence

Usage:
  python omniscient_cli.py query --company "Arch Reinsurance" --question "What are the risks?"
  python omniscient_cli.py analyze --company "Arch Reinsurance"
  python omniscient_cli.py compare --companies "Arch Reinsurance" "Aspen Bermuda"
  python omniscient_cli.py search --criteria "high leverage"
  python omniscient_cli.py opportunities
  python omniscient_cli.py risks --company "Arch Reinsurance"
"""

import sys
import json
import argparse
from typing import Optional

try:
    from omniscient_bot import get_bot
    from data_loader import get_loader
except ImportError:
    print("Error: Required modules not found. Ensure you're in the bma-filings directory.")
    sys.exit(1)


def print_result(result: dict, title: str = "Result"):
    """Pretty print bot results."""
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print(f"{'=' * 70}\n")

    if result.get('status') != 'success':
        print(f"❌ Error: {result.get('analysis', result.get('error', 'Unknown error'))}\n")
        return

    # Main content
    content_key = None
    for key in ['analysis', 'comparison', 'results', 'opportunities', 'assessment']:
        if key in result:
            content_key = key
            break

    if content_key:
        print(result[content_key])
    else:
        print(json.dumps(result, indent=2))

    # Footer with audit info
    if result.get('audit_id'):
        print(f"\n{'─' * 70}")
        confidence = result.get('confidence', 'N/A')
        audit_id = result.get('audit_id')
        risk_level = result.get('risk_level', '')

        footer = f"Audit ID: {audit_id}"
        if confidence:
            footer += f" | Confidence: {confidence}%"
        if risk_level:
            footer += f" | Risk Level: {risk_level}"

        print(footer)
    print()


def cmd_query(company: str, question: str, year: Optional[int] = None):
    """Query bot about a company."""
    try:
        bot = get_bot()
        result = bot.query(company, question, year)
        print_result(result, f"Bot Analysis: {company}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_analyze(company: str, metrics: Optional[list] = None, year: Optional[int] = None):
    """Perform deep analysis."""
    try:
        bot = get_bot()
        metrics = metrics or ['financial', 'risk']
        result = bot.analyze_company(company, year, metrics)
        print_result(result, f"Deep Analysis: {company}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_compare(companies: list, year: Optional[int] = None):
    """Compare multiple companies."""
    if len(companies) < 2:
        print("❌ Error: Need at least 2 companies for comparison\n")
        sys.exit(1)

    try:
        bot = get_bot()
        result = bot.compare_companies(companies, year)
        print_result(result, f"Company Comparison: {' vs '.join(companies)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_search(criteria: str):
    """Search companies by criteria."""
    try:
        bot = get_bot()
        result = bot.search_companies(criteria)
        print_result(result, f"Company Search: {criteria}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_opportunities():
    """Identify investment opportunities."""
    try:
        bot = get_bot()
        result = bot.identify_opportunities()
        print_result(result, "Investment Opportunities")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_risks(company: str, year: Optional[int] = None):
    """Perform risk assessment."""
    try:
        bot = get_bot()
        result = bot.risk_assessment(company, year)
        print_result(result, f"Risk Assessment: {company}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def cmd_list():
    """List available companies."""
    try:
        loader = get_loader()
        companies = loader.get_all_companies()

        print(f"\n{'=' * 70}")
        print(f" Available Companies ({len(companies)} total)")
        print(f"{'=' * 70}\n")

        # Print in 3 columns
        cols = 3
        for i, company in enumerate(sorted(companies)):
            print(f"{company:<30}", end="")
            if (i + 1) % cols == 0:
                print()

        print(f"\n{'─' * 70}")
        print(f"Use: python omniscient_cli.py <command> --company \"<name>\"\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Omniscient Bot CLI - AI-powered company analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Query bot:        python omniscient_cli.py query --company "Arch Reinsurance" --question "What are risks?"
  Analyze company:  python omniscient_cli.py analyze --company "Arch Reinsurance"
  Compare companies: python omniscient_cli.py compare --companies "Arch" "Aspen" "AXIS"
  Search companies:  python omniscient_cli.py search --criteria "high leverage"
  Risk assessment:   python omniscient_cli.py risks --company "Arch Reinsurance"
  Find opportunities: python omniscient_cli.py opportunities
  List companies:   python omniscient_cli.py list
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Query command
    query_parser = subparsers.add_parser('query', help='Ask bot a question')
    query_parser.add_argument('--company', required=True, help='Company name')
    query_parser.add_argument('--question', required=True, help='Question to ask')
    query_parser.add_argument('--year', type=int, help='Financial year')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Deep company analysis')
    analyze_parser.add_argument('--company', required=True, help='Company name')
    analyze_parser.add_argument('--metrics', nargs='+', help='Metrics to analyze')
    analyze_parser.add_argument('--year', type=int, help='Financial year')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare companies')
    compare_parser.add_argument('--companies', nargs='+', required=True, help='Companies to compare')
    compare_parser.add_argument('--year', type=int, help='Financial year')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search companies')
    search_parser.add_argument('--criteria', required=True, help='Search criteria')

    # Risks command
    risks_parser = subparsers.add_parser('risks', help='Risk assessment')
    risks_parser.add_argument('--company', required=True, help='Company name')
    risks_parser.add_argument('--year', type=int, help='Financial year')

    # Opportunities command
    subparsers.add_parser('opportunities', help='Find investment opportunities')

    # List command
    subparsers.add_parser('list', help='List available companies')

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to command handler
    if args.command == 'query':
        cmd_query(args.company, args.question, args.year)
    elif args.command == 'analyze':
        cmd_analyze(args.company, args.metrics, args.year)
    elif args.command == 'compare':
        cmd_compare(args.companies, args.year)
    elif args.command == 'search':
        cmd_search(args.criteria)
    elif args.command == 'risks':
        cmd_risks(args.company, args.year)
    elif args.command == 'opportunities':
        cmd_opportunities()
    elif args.command == 'list':
        cmd_list()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
