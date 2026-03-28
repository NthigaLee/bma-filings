#!/usr/bin/env python3
"""
PDF Financial Statement Parser
Extracts financial statement data from PDF files with source page tracking.
Uses pdfplumber for superior table extraction from financial statements.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pdfplumber


class PDFStatementParser:
    """Parser for insurance/reinsurance financial statements in PDF format."""

    def __init__(self):
        self.pdf_root = Path(__file__).parent / 'pdfs'

    def extract_pdf_with_pdfplumber(self, pdf_path: str) -> Tuple[Dict[int, str], Dict[int, List[Dict]]]:
        """
        Extract text and tables from PDF with page tracking using pdfplumber.

        Returns:
            Tuple of (pages_text dict, pages_tables dict)
        """
        try:
            pages_text = {}
            pages_tables = {}

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        pages_text[page_num] = text

                    # Extract tables
                    try:
                        tables = page.extract_tables()
                        if tables:
                            pages_tables[page_num] = tables
                    except Exception as table_err:
                        # Some pages might not have tables, that's ok
                        pass

            return pages_text, pages_tables
        except Exception as e:
            print(f"Error extracting PDF {pdf_path}: {e}")
            return {}, {}

    def extract_company_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Extract company name and year from PDF filename.

        Expected format: YYYY-MM-DD-HH-MM-SS-CompanyName---YearFinancialStatement.pdf
        Example: 2020-09-30-11-53-38-Qatar-Reinsurance-Company-Limited---2019-Financial-Statements.pdf
        """
        try:
            # Remove .pdf extension
            name_without_ext = filename.replace('.pdf', '')

            # Split by ---
            parts = name_without_ext.split('---')

            if len(parts) >= 2:
                # parts[0] = "YYYY-MM-DD-HH-MM-SS-CompanyName"
                # parts[1] = "YearFinancialStatement" or similar

                date_company_part = parts[0]
                year_statement_part = parts[1]

                # Extract company name: remove timestamp (YYYY-MM-DD-HH-MM-SS-)
                # Timestamp is 19 characters + 1 dash = 20 chars total
                if len(date_company_part) > 20:
                    company_name = date_company_part[20:].replace('-', ' ').strip()
                else:
                    company_name = date_company_part.replace('-', ' ').strip()

                # Extract year from second part (should be YearXXX format)
                year = None
                year_match = re.search(r'^(\d{4})', year_statement_part)
                if year_match:
                    year = int(year_match.group(1))

                # If no year found, search anywhere in filename
                if not year:
                    year_match = re.search(r'(\d{4})', filename)
                    if year_match:
                        year = int(year_match.group(1))

                return {
                    'filename': filename,
                    'company': company_name if company_name else 'Unknown',
                    'year': year if year else 2024,
                    'raw_filename': filename
                }
        except Exception as e:
            print(f"Error parsing filename {filename}: {e}")

        return {
            'filename': filename,
            'company': 'Unknown',
            'year': 2024,
            'raw_filename': filename
        }

    def find_financial_statement_pages(self, pages_text: Dict[int, str]) -> Dict[str, int]:
        """
        Identify which pages contain balance sheet, income statement, etc.

        Returns:
            Dict mapping statement type to starting page number
        """
        statement_pages = {
            'balance_sheet': None,
            'income_statement': None,
            'financial_notes': None,
            'cash_flow': None,
        }

        keywords = {
            'balance_sheet': ['balance sheet', 'statement of financial position', 'assets'],
            'income_statement': ['income statement', 'statement of earnings', 'statement of operations'],
            'cash_flow': ['cash flow', 'statement of cash flows'],
            'financial_notes': ['notes to financial statements', 'notes (unaudited)', 'accounting policies'],
        }

        for page_num, text in pages_text.items():
            text_lower = text.lower()

            for stmt_type, keywords_list in keywords.items():
                # Skip if already found
                if statement_pages[stmt_type]:
                    continue

                for keyword in keywords_list:
                    if keyword in text_lower:
                        statement_pages[stmt_type] = page_num
                        break

        return statement_pages

    def extract_financial_section(self, pages_text: Dict[int, str], section_keywords: List[str], validate_fn=None) -> Tuple[Optional[int], str]:
        """
        Find and extract a financial statement section (Balance Sheet, Income Statement, etc.)
        Uses both keywords and validation function to find the actual statement page.
        Returns (page_number, section_text)
        """
        candidates = []

        for page_num, text in pages_text.items():
            text_lower = text.lower()
            # Check if this page contains the section keywords
            if any(kw in text_lower for kw in section_keywords):
                candidates.append((page_num, text))

        # If we have candidates, validate them to find the actual statement page
        if not candidates:
            return None, ""

        # If validation function provided, use it to pick the best candidate
        if validate_fn:
            for page_num, text in candidates:
                if validate_fn(text):
                    return page_num, text

        # Return first candidate if no validation provided
        return candidates[0][0], candidates[0][1]

    def parse_financial_value(self, value_str: str) -> Optional[float]:
        """
        Parse currency values from financial statements.
        Handles formats like: $2,289,373, (1,234.56), 1234567, etc.
        """
        if not value_str:
            return None

        value_str = value_str.strip()

        # Check for negative (parentheses)
        is_negative = value_str.startswith('(') and value_str.endswith(')')

        # Remove all non-numeric characters except decimal point
        cleaned = ''.join(c for c in value_str if c.isdigit() or c == '.')

        try:
            if cleaned:
                value = float(cleaned)
                return -value if is_negative else value
        except ValueError:
            pass

        return None

    def extract_balance_sheet_from_text(self, pages_text: Dict[int, str]) -> Dict[str, Dict[str, Any]]:
        """
        Extract balance sheet line items from formatted text.
        Handles multi-line entries where item name and numbers are on different lines.
        """
        balance_sheet = {}

        # Find balance sheet section - validate by checking for "Total assets" and "Total liabilities"
        def has_bs_data(text):
            text_lower = text.lower()
            return bool(
                re.search(r'total\s+assets?', text_lower) and
                re.search(r'total\s+liabilit', text_lower)
            )

        bs_keywords = ['balance sheet', 'statement of financial position', 'balance sheets', 'assets']
        bs_page, bs_text = self.extract_financial_section(pages_text, bs_keywords, validate_fn=has_bs_data)

        if not bs_page:
            return balance_sheet

        lines = bs_text.split('\n')

        # Balance sheet line items - PRIORITIZED BASELINE (CRITICAL for accuracy)
        # Priority 1: Core equation (Assets = Liabilities + Equity)
        # Priority 2: Insurance contract liabilities (multiple naming conventions)
        # Priority 3: Cash, Investments, and key components
        # Format: (item_keywords, normalized_name)
        items = [
            # PRIORITY 1: CORE EQUATION ITEMS
            ([r'total.*assets?(?!\s+held)'], 'Total Assets'),
            ([r'total.*liabilities?(?!\s+and)'], 'Total Liabilities'),
            ([r'total.*stockholders?.*equity|total.*shareholders?.*equity'], 'Total Shareholders Equity'),
            ([r'total.*liabilities?.*and.*(?:stockholders?|shareholders?).*equity'], 'Total Liabilities and Equity'),

            # PRIORITY 2: INSURANCE CONTRACT LIABILITIES (multiple naming conventions)
            # These are critical for understanding insurance company balance sheets
            ([r'insurance.*contract.*liabilities?', r'reinsurance.*contract.*liabilities?'], 'Insurance Contract Liabilities'),
            ([r'loss.*and.*lae|lae.*expense', r'loss.*adjustment.*expense'], 'Loss and LAE Reserves'),
            ([r'reserve.*for.*claims?', r'claims?.*reserve'], 'Claims Reserves'),
            ([r'gross.*reserves?|loss.*reserves?'], 'Loss Reserves'),
            ([r'unearned.*premiums?'], 'Unearned Premiums'),
            ([r'policy.*reserves?'], 'Policy Reserves'),
            ([r'investment.*contract.*discretionary'], 'Investment Contracts with Discretionary Participation'),

            # PRIORITY 3: CASH (including restricted cash)
            ([r'restricted.*cash'], 'Restricted Cash'),
            ([r'cash.*and.*cash.*equivalents?|cash.*equivalents?'], 'Cash and Cash Equivalents'),
            ([r'(?<!restricted\s)cash(?!\s+flow)'], 'Cash'),

            # PRIORITY 3: INVESTMENTS (types and total)
            (['total.*investments?'], 'Total Investments'),
            (['fixed.*maturity|fixed.*income.*investments?'], 'Fixed Income Investments'),
            (['equity.*securities?|equity.*investments?'], 'Equity Investments'),
            (['real.*estate.*investments?'], 'Real Estate Investments'),
            (['mortgage.*backed.*securities?'], 'Mortgage-Backed Securities'),

            # Key Assets
            (['premium.*receivable', 'premiums?.*receivable'], 'Premiums Receivable'),
            (['reinsurance.*recoverable'], 'Reinsurance Recoverable'),
            (['prepaid.*reinsurance'], 'Prepaid Reinsurance Premiums'),
            (['deferred.*acquisition.*costs?'], 'Deferred Acquisition Costs'),
            (['accrued.*investment.*income'], 'Accrued Investment Income'),
            (['receivable.*for.*investments?.*sold'], 'Receivable for Investments Sold'),
            (['other.*assets?'], 'Other Assets'),

            # Key Liabilities
            (['reinsurance.*payable'], 'Reinsurance Payable'),
            (['accounts?.*payable'], 'Accounts Payable'),
            (['due.*to.*affiliates?'], 'Due to Affiliates'),
            (['other.*liabilities?'], 'Other Liabilities'),
            (['payable.*for.*investments?.*purchased'], 'Payable for Investments Purchased'),

            # Equity Components
            (['common.*stock|ordinary.*shares?'], 'Common Stock'),
            (['additional.*paid.?in.*capital|paid.?in.*capital'], 'Additional Paid-in Capital'),
            (['retained.*earnings?'], 'Retained Earnings'),
            (['accumulated.*comprehensive.*income'], 'Accumulated Other Comprehensive Income'),
        ]

        # Process each item
        for keywords, item_name in items:
            # Find the line that matches this item
            matching_line_idx = None
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Check if any keyword matches
                if any(re.search(kw, line_lower) for kw in keywords):
                    matching_line_idx = i
                    break

            if matching_line_idx is None:
                continue

            # Extract the value from this line
            value_str = lines[matching_line_idx]

            # Extract all numbers and filter for financial amounts
            # Financial statement values are typically >= 100 (in thousands)
            all_numbers = re.findall(r'[\d,]+(?:\.\d+)?', value_str)
            financial_values = []
            for num_str in all_numbers:
                val = self.parse_financial_value(num_str)
                # Keep numbers >= 100 (representing financial amounts in thousands)
                if val and val >= 100:
                    financial_values.append((num_str, val))

            if financial_values:
                # Use the first substantial financial value (most recent year first)
                value = financial_values[0][1]
                balance_sheet[item_name] = {
                    'value': int(value) if value.is_integer() else value,
                    'page': bs_page,
                    'line_item': item_name,
                    'raw_line': value_str[:100]
                }

        return balance_sheet

    def validate_fundamental_equation(self, balance_sheet: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the fundamental accounting equation: Total Assets = Total Liabilities + Total Shareholders Equity
        Returns validation results with differences and notes.
        """
        validation = {
            'equation_valid': False,
            'has_all_components': False,
            'total_assets': None,
            'total_liabilities': None,
            'total_equity': None,
            'difference': None,
            'difference_pct': None,
            'notes': []
        }

        # Extract the key values
        total_assets = balance_sheet.get('Total Assets', {}).get('value')
        total_liabilities = balance_sheet.get('Total Liabilities', {}).get('value')
        total_equity = balance_sheet.get('Total Shareholders Equity', {}).get('value')

        validation['total_assets'] = total_assets
        validation['total_liabilities'] = total_liabilities
        validation['total_equity'] = total_equity

        # Check if we have all components
        if all([total_assets, total_liabilities, total_equity]):
            validation['has_all_components'] = True

            # Calculate the right-hand side of the equation
            liab_plus_equity = total_liabilities + total_equity

            # Check if equation balances (allowing for rounding differences)
            difference = abs(total_assets - liab_plus_equity)
            difference_pct = (difference / total_assets * 100) if total_assets else 0

            validation['difference'] = difference
            validation['difference_pct'] = difference_pct

            # Allow for small rounding differences (< 0.1%)
            if difference_pct < 0.1:
                validation['equation_valid'] = True
                validation['notes'].append('Equation balances within 0.1% tolerance')
            elif difference_pct < 1:
                validation['notes'].append(f'Equation near balance (difference: {difference_pct:.2f}%)')
            else:
                validation['notes'].append(f'Equation out of balance (difference: {difference_pct:.2f}%)')
        else:
            missing = []
            if not total_assets:
                missing.append('Total Assets')
            if not total_liabilities:
                missing.append('Total Liabilities')
            if not total_equity:
                missing.append('Total Shareholders Equity')
            validation['notes'].append(f'Missing: {", ".join(missing)}')

        return validation

    def extract_income_statement_from_text(self, pages_text: Dict[int, str]) -> Dict[str, Dict[str, Any]]:
        """
        Extract income statement line items from formatted text.
        """
        income_statement = {}

        # Find income statement section - validate by checking for multiple income statement indicators
        def has_is_data(text):
            text_lower = text.lower()
            # Must have Net income/earnings AND either premiums or total revenues/expenses
            has_net_income = re.search(r'net\s+income|net\s+earnings?', text_lower)
            has_revenue_section = re.search(r'revenue|premium|earnings', text_lower)
            has_expense_section = re.search(r'expense|cost|loss', text_lower)

            return bool(has_net_income and has_revenue_section and has_expense_section)

        is_keywords = [
            'income statement',
            'statement of earnings',
            'statement of operations',
            'statements of operations',
            'revenues',
            'premiums written'
        ]
        is_page, is_text = self.extract_financial_section(pages_text, is_keywords, validate_fn=has_is_data)

        if not is_page:
            return income_statement

        lines = is_text.split('\n')

        # Comprehensive income statement line items
        # Ordered by specificity (most specific first) to avoid duplicate matches
        items = [
            # Gross Premiums & Revenue - most specific patterns first
            (['gross premium.*written'], 'Gross Premiums Written'),
            (['net premium.*written'], 'Net Premiums Written'),
            (['ceded premium', 'reinsurance premium'], 'Ceded Premiums'),
            (['increase.*unearned premium', 'decrease.*unearned premium', 'change.*unearned premium'], 'Change in Unearned Premiums'),
            (['net premium.*earned'], 'Net Premiums Earned'),

            # Investment Income - specific patterns with full line matching
            (['net realized.*unrealized'], 'Net Realized and Unrealized Gains/Losses'),  # Matches combined line
            (['net.*foreign exchange.*gain'], 'Foreign Exchange Gains'),
            (['net.*foreign exchange.*loss'], 'Foreign Exchange Losses'),
            (['net investment income'], 'Net Investment Income'),
            (['other income'], 'Other Income'),

            # Total Revenue
            (['total revenue', 'total income'], 'Total Revenues'),

            # Claims & Expenses
            (['net claim.*expense', 'claims.*claim expense', 'net.*claim.*incurred'], 'Net Claims and Claim Expenses'),
            (['acquisition expense'], 'Acquisition Expenses'),
            (['operational expense', 'operating expense'], 'Operational Expenses'),
            (['corporate expense', 'administrative expense'], 'Corporate Expenses'),
            (['general.*administrative', 'sg&a'], 'General and Administrative Expenses'),

            # Total Expenses
            (['total expense'], 'Total Expenses'),

            # Bottom Line
            (['income.*before.*tax', 'earnings.*before.*tax'], 'Income Before Taxes'),
            (['income tax.*expense', 'income tax.*benefit', 'provision.*income tax'], 'Income Tax Expense'),
            (['net income'], 'Net Income'),
        ]

        # Track which lines have been matched to avoid duplicates
        matched_lines = set()

        # Process each item, preferring more specific patterns first
        for keywords, item_name in items:
            matching_line_idx = None
            for i, line in enumerate(lines):
                # Skip lines already matched
                if i in matched_lines:
                    continue

                line_lower = line.lower()
                if any(re.search(kw, line_lower) for kw in keywords):
                    matching_line_idx = i
                    break

            if matching_line_idx is None:
                continue

            # Mark this line as matched
            matched_lines.add(matching_line_idx)

            # Extract numbers from the line and filter for financial amounts
            all_numbers = re.findall(r'[\d,]+(?:\.\d+)?', lines[matching_line_idx])
            financial_values = []
            for num_str in all_numbers:
                val = self.parse_financial_value(num_str)
                # Keep numbers >= 100 (representing financial amounts in thousands)
                if val and val >= 100:
                    financial_values.append((num_str, val))

            if financial_values:
                # Use the first substantial financial value (most recent year first)
                value = financial_values[0][1]
                income_statement[item_name] = {
                    'value': int(value) if value.is_integer() else value,
                    'page': is_page,
                    'line_item': item_name,
                    'raw_line': lines[matching_line_idx][:100]
                }

        return income_statement

    def extract_financial_notes(self, pages_text: Dict[int, str], notes_page: int) -> Dict[str, Any]:
        """
        Extract financial notes from PDF.
        """
        notes = {}

        if notes_page not in pages_text:
            return notes

        text = pages_text[notes_page]

        # Extract key note sections
        sections = {
            'accounting_policies': r'(1\.\s+(?:Summary of|Accounting)\s+.*?(?=\d+\.|$))',
            'significant_events': r'(Subsequent Events.*?(?=\d+\.|$))',
            'risk_factors': r'(Risk.*?(?=\d+\.|$))',
        }

        for section_name, pattern in sections.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1)[:500]  # Limit to first 500 chars
                notes[section_name] = {
                    'content': content,
                    'page': notes_page
                }

        return notes

    def extract_cash_flow_from_text(self, pages_text: Dict[int, str], cf_page: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract cash flow statement items from text.
        Organizes by Operating, Investing, and Financing activities.
        """
        cash_flow = {}

        if not cf_page or cf_page not in pages_text:
            return cash_flow

        cf_text = pages_text[cf_page]
        lines = cf_text.split('\n')

        # Cash flow line items organized by section
        items = [
            # Operating Activities
            ([r'net.*income|net.*loss'], 'Net Income'),
            ([r'depreciation.*amortization|amortization.*depreciation'], 'Depreciation and Amortization'),
            ([r'stock.?based.*compensation'], 'Stock-based Compensation'),
            ([r'changes?.*(?:in\s+)?(?:current\s+)?assets?.*liabilit|changes?.*working.*capital'], 'Changes in Working Capital'),
            ([r'other.*operating'], 'Other Operating Activities'),

            # Investing Activities
            ([r'(?:purchases?|investment|acquisitions?)\s+(?:of\s+)?(?:fixed|property|equipment|securities)'], 'Property and Equipment Purchases'),
            ([r'(?:sales?|proceeds?)\s+(?:from|of)\s+(?:investments?|securities)'], 'Proceeds from Investment Sales'),
            ([r'(?:purchases?|acquisitions?)\s+(?:of\s+)?investments?'], 'Investment Purchases'),
            ([r'other.*investing'], 'Other Investing Activities'),

            # Financing Activities
            ([r'dividends?.*paid'], 'Dividends Paid'),
            ([r'(?:issuance|proceeds?)\s+(?:of\s+)?(?:debt|borrowing|bonds?)'], 'Debt Issuance'),
            ([r'(?:repayment|repurchase)\s+(?:of\s+)?(?:debt|borrowing|bonds?)'], 'Debt Repayment'),
            ([r'(?:issuance|proceeds?)\s+(?:from\s+)?(?:stock|equity|shares?)'], 'Stock Issuance'),
            ([r'(?:repurchase|buyback)\s+(?:of\s+)?(?:stock|shares?)'], 'Stock Repurchase'),
            ([r'other.*financing'], 'Other Financing Activities'),

            # Bottom line
            ([r'net\s+(?:increase|decrease|change)\s+in\s+cash'], 'Net Change in Cash'),
            ([r'cash.*beginning.*period|opening.*cash'], 'Cash at Beginning of Period'),
            ([r'cash.*end.*period|closing.*cash'], 'Cash at End of Period'),
        ]

        # Process each item
        for keywords, item_name in items:
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(re.search(kw, line_lower) for kw in keywords):
                    # Extract numbers from this line
                    numbers = re.findall(r'[\d,]+(?:\.\d+)?', line)
                    for num_str in numbers:
                        val = self.parse_financial_value(num_str)
                        if val and val >= 100:  # Financial values in thousands
                            cash_flow[item_name] = {
                                'value': val,
                                'page': cf_page,
                                'raw_line': line[:100]
                            }
                            break
                    break

        return cash_flow

    def extract_mda_sections(self, pages_text: Dict[int, str], mda_start_page: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract Management Discussion and Analysis (MD&A) organized by subsection.
        Extracts structured summaries with key themes and metrics.
        """
        mda = {}

        if not mda_start_page:
            # Search for MD&A section
            for page_num, text in pages_text.items():
                if re.search(r"management'?s?\s+discussion.*analysis|md&a|financial\s+condition.*results\s+of\s+operations", text, re.IGNORECASE):
                    mda_start_page = page_num
                    break

        if not mda_start_page or mda_start_page not in pages_text:
            return mda

        # Get MD&A text - typically spans multiple pages
        mda_text = ''
        for page_num in sorted([p for p in pages_text.keys() if p >= mda_start_page])[:10]:  # Get up to 10 pages of MD&A
            mda_text += pages_text[page_num] + '\n'

        # Parse by subsections
        subsections = {
            'Business Overview': r"(business\s+overview|executive\s+summary|company\s+description)(.*?)(?=(?:financial|results|risk|liquidity|capital))",
            'Financial Condition': r"(financial\s+condition|liquidity.*capital\s+resources)(.*?)(?=results\s+of\s+operations|risk)",
            'Results of Operations': r"(results?\s+of\s+operations|operating\s+performance)(.*?)(?=risk|liquidity|outlook)",
            'Risks and Uncertainties': r"(risk(?:s|\s+factor)?|uncertainties)(.*?)(?=outlook|off.balance|subsequent)",
            'Off-Balance Sheet': r"(off.balance\s+sheet|off-balance\s+sheet|special\s+purpose)(.*?)(?=outlook|subsequent|critical)",
            'Outlook': r"(outlook|forward.looking|future\s+prospects?)(.*?)(?=$|\n\n)"
        }

        for section_name, pattern in subsections.items():
            match = re.search(pattern, mda_text, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract key content - limit to avoid storing entire narrative
                content = match.group(2)[:2000] if match.lastindex >= 2 else match.group(0)[:2000]
                # Extract key metrics if any numeric values present
                metrics = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:%|million|thousand|dollars?)?', content)
                mda[section_name] = {
                    'summary': content,
                    'page_start': mda_start_page,
                    'key_metrics_found': metrics[:5] if metrics else []
                }

        return mda

    def extract_all_financial_notes(self, pages_text: Dict[int, str], notes_page: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract ALL financial notes organized by note number (not truncated).
        Handles notes with multiple pages.
        """
        notes = {}

        if not notes_page:
            # Find notes section
            for page_num, text in pages_text.items():
                if re.search(r"notes?\s+to\s+financial|notes?\s+\(unaudited\)|accounting\s+policies", text, re.IGNORECASE):
                    notes_page = page_num
                    break

        if not notes_page or notes_page not in pages_text:
            return notes

        # Collect all notes text - typically spans multiple pages
        notes_text = ''
        for page_num in sorted([p for p in pages_text.keys() if p >= notes_page])[:30]:  # Get up to 30 pages of notes
            notes_text += pages_text[page_num] + '\n'

        # Parse notes by number/letter
        # Pattern: Note 1, Note A, NOTE 1., etc.
        note_pattern = r'(?:note|NOTE)\s+([0-9A-Z]{1,2})[.):\s]+(.*?)(?=(?:Note|NOTE)\s+[0-9A-Z]{1,2}[.):\s]|$)'

        matches = re.finditer(note_pattern, notes_text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            note_num = match.group(1)
            note_content = match.group(2)

            # Extract first line as note title (usually after the number)
            title_match = re.search(r'^([^.\n]+)', note_content)
            note_title = title_match.group(1) if title_match else f'Note {note_num}'

            # Find tables within this note
            tables = []
            table_pattern = r'(\d+\s*\d+\s*\d+(?:\s+[(\d].*?)*)'  # Simple table detection

            notes[f'Note {note_num}'] = {
                'title': note_title,
                'content': note_content[:3000],  # Store up to 3000 chars per note (much larger than before)
                'page_start': notes_page,
                'has_tables': bool(re.search(r'\d+\s+\d+\s+\d+', note_content))
            }

        return notes

    def extract_segment_data(self, pages_text: Dict[int, str], notes_page: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract segment reporting data (geographic, product line, etc.)
        Usually found in financial notes.
        """
        segments = {}

        # Search for segment note in notes section
        for page_num, text in pages_text.items():
            if re.search(r"segment|geographic|product\s+line|business\s+line", text, re.IGNORECASE):
                # Look for segment tables and data
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if re.search(r"segment|geographic|product\s+line", line, re.IGNORECASE):
                        # Collect next 20 lines for segment data
                        segment_text = '\n'.join(lines[i:min(i+20, len(lines))])

                        # Try to parse segment breakdown
                        seg_match = re.search(r"bermuda|bermuda\s+and|us|usa|europe|international", segment_text, re.IGNORECASE)
                        if seg_match:
                            segments['Geographic'] = {
                                'content': segment_text[:1000],
                                'page': page_num
                            }
                            break

        return segments

    def extract_investment_composition(self, pages_text: Dict[int, str], notes_page: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract investment portfolio composition detail (Fixed Income, Equity, Real Estate, etc.)
        Usually in balance sheet notes or separate schedule.
        """
        investments = {}

        # Search for investment schedule
        for page_num, text in pages_text.items():
            if re.search(r"investment\s+schedule|investments?\s+at|portfolio\s+composition", text, re.IGNORECASE):
                lines = text.split('\n')

                investment_types = {
                    'Fixed Income': [r'fixed\s+maturity|fixed\s+income|bonds?|government|corporate'],
                    'Equity': [r'equity\s+securities?|stock|common\s+stock|preferred\s+stock'],
                    'Real Estate': [r'real\s+estate|property|real\s+estate\s+investments?'],
                    'Derivatives': [r'derivative|futures|options?|swaps?'],
                    'Mortgage-Backed': [r'mortgage.?backed|mbs'],
                    'Cash Equivalents': [r'cash\s+equivalent|money\s+market|short.?term']
                }

                for inv_type, keywords in investment_types.items():
                    for line in lines:
                        if any(re.search(kw, line, re.IGNORECASE) for kw in keywords):
                            numbers = re.findall(r'[\d,]+(?:\.\d+)?', line)
                            for num_str in numbers:
                                val = self.parse_financial_value(num_str)
                                if val and val >= 100:
                                    investments[inv_type] = {
                                        'value': val,
                                        'page': page_num,
                                        'raw_line': line[:100]
                                    }
                                    break
                            if inv_type in investments:
                                break

        return investments

    def extract_ownership_structure(self, pages_text: Dict[int, str]) -> Dict[str, Any]:
        """
        Extract ownership structure information from PDF.
        """
        ownership = {
            'ownership_type': 'Unknown',
            'domicile': 'Bermuda',  # Default for BMA companies
            'regulatory_body': 'BMA',
            'primary_shareholders': [],
            'share_structure': {}
        }

        # Search all pages for ownership information
        full_text = ' '.join(pages_text.values()).lower()

        if 'public' in full_text:
            ownership['ownership_type'] = 'Public'
        elif 'private' in full_text:
            ownership['ownership_type'] = 'Private'

        # Search for specific domicile
        if 'bermuda' in full_text:
            ownership['domicile'] = 'Bermuda'
        elif 'cayman' in full_text:
            ownership['domicile'] = 'Cayman Islands'
        elif 'delaware' in full_text:
            ownership['domicile'] = 'Delaware'

        return ownership

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse complete financial statements from PDF.

        Returns:
            Dictionary containing:
            - metadata (company, year, source PDF)
            - balance_sheet (with page citations)
            - income_statement (with page citations)
            - financial_notes (with page citations)
            - ownership_structure
            - extraction_date
            - extraction_stats (how many items extracted)
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return {'error': f'PDF not found: {pdf_path}'}

        # Extract text with page tracking using pdfplumber
        pages_text, pages_tables = self.extract_pdf_with_pdfplumber(str(pdf_path))

        if not pages_text:
            return {'error': f'Could not extract text from {pdf_path}'}

        # Extract metadata
        metadata = self.extract_company_metadata(pdf_path.name)

        # Find statement pages
        statement_pages = self.find_financial_statement_pages(pages_text)

        # Extract financial data using improved text-based parsing
        balance_sheet = self.extract_balance_sheet_from_text(pages_text)
        income_statement = self.extract_income_statement_from_text(pages_text)
        financial_notes = {}

        if statement_pages['financial_notes']:
            financial_notes = self.extract_all_financial_notes(
                pages_text,
                statement_pages['financial_notes']
            )

        # Extract NEW sections: Cash Flow, MD&A, Segments, Investments
        cash_flow = {}
        if statement_pages['cash_flow']:
            cash_flow = self.extract_cash_flow_from_text(
                pages_text,
                statement_pages['cash_flow']
            )

        mda = self.extract_mda_sections(pages_text)
        segments = self.extract_segment_data(pages_text, statement_pages['financial_notes'])
        investments = self.extract_investment_composition(pages_text, statement_pages['financial_notes'])

        # Extract ownership
        ownership = self.extract_ownership_structure(pages_text)

        # Validate fundamental equation
        equation_validation = self.validate_fundamental_equation(balance_sheet)

        # Compile result
        result = {
            'metadata': metadata,
            'balance_sheet': balance_sheet,
            'income_statement': income_statement,
            'cash_flow': cash_flow,
            'management_discussion_analysis': mda,
            'financial_notes': financial_notes,
            'segments': segments,
            'investments': investments,
            'ownership_structure': ownership,
            'statement_pages': statement_pages,
            'source_pdf': pdf_path.name,
            'extraction_stats': {
                'balance_sheet_items': len(balance_sheet),
                'income_statement_items': len(income_statement),
                'cash_flow_items': len(cash_flow),
                'mda_sections': len(mda),
                'financial_notes_sections': len(financial_notes),
                'total_pages': len(pages_text)
            },
            'equation_validation': equation_validation,
            'extraction_date': __import__('datetime').datetime.now(
                __import__('datetime').timezone.utc
            ).isoformat()
        }

        return result


def main():
    """Test PDF parser on a sample PDF."""
    parser = PDFStatementParser()

    # Find first PDF in pdfs directory
    pdf_dir = Path(__file__).parent / 'pdfs'
    pdfs = list(pdf_dir.glob('*.pdf'))

    if pdfs:
        print(f"Testing on: {pdfs[0].name}")
        result = parser.parse_pdf(str(pdfs[0]))

        if 'error' not in result:
            print(f"Company: {result['metadata']['company']}")
            print(f"Year: {result['metadata']['year']}")
            print(f"Balance sheet items found: {len(result['balance_sheet'])}")
            print(f"Income statement items found: {len(result['income_statement'])}")

            # Show sample data
            if result['balance_sheet']:
                item = list(result['balance_sheet'].items())[0]
                print(f"\nSample balance sheet item:")
                print(f"  {item[0]}: ${item[1]['value']:,} (Page {item[1]['page']})")
        else:
            print(f"Error: {result['error']}")
    else:
        print("No PDFs found in pdfs directory")


if __name__ == '__main__':
    main()
