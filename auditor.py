#!/usr/bin/env python3
"""
Auditor Module
Financial validation and audit trail management
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from data_loader import get_loader

REPO_ROOT = Path(__file__).parent
AUDIT_LOG_PATH = REPO_ROOT / 'data' / 'audit_log.json'


class FinancialAuditor:
    """Validates financial data and maintains audit trail."""

    def __init__(self):
        self.data_loader = get_loader()
        self.audit_log = self._load_audit_log()

    def _load_audit_log(self) -> Dict:
        """Load existing audit log."""
        if AUDIT_LOG_PATH.exists():
            with open(AUDIT_LOG_PATH, 'r') as f:
                return json.load(f)
        return {}

    def _save_audit_log(self):
        """Save audit log to file."""
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_PATH, 'w') as f:
            json.dump(self.audit_log, f, indent=2)

    def _create_audit_id(self) -> str:
        """Generate unique audit ID."""
        return str(uuid.uuid4())[:12]

    # ═══════════════════════════════════════════════════════════════
    # VALIDATION CHECKS
    # ═══════════════════════════════════════════════════════════════

    def check_mathematical_consistency(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Verify that calculations are consistent (totals = sum of components).

        Returns:
            (passed: bool, findings: List[str])
        """
        findings = []

        # Check income statement totals
        inc = data.get('income_statement', {})
        if inc:
            # Total Revenues should equal key components
            total_rev = inc.get('Total Revenues', 0)
            premiums = inc.get('Net Premiums Earned', 0)
            investment = inc.get('Net Investment Income', 0)

            if total_rev > 0 and premiums > 0:
                if abs(total_rev - (premiums + investment + inc.get('Investment Gains/Losses', 0))) > 0.01 * total_rev:
                    findings.append("Income: Total Revenues does not match sum of components")

            # Net Income should equal Revenues - Expenses
            net_income = inc.get('Net Income', 0)
            total_rev = inc.get('Total Revenues', 0)
            total_exp = inc.get('Total Expenses', 0)

            if total_rev > 0 and total_exp > 0:
                expected = total_rev - total_exp
                if abs(net_income - expected) > 0.01 * abs(expected):
                    findings.append("Income: Net Income does not equal Revenues - Expenses")

        # Check balance sheet totals
        bs = data.get('balance_sheet', {})
        if bs:
            # Total Assets should equal Liabilities + Equity
            total_assets = bs.get('Total Assets', 0)
            total_liab = bs.get('Total Liabilities', 0)
            total_equity = bs.get('Total Equity', 0)

            if total_assets > 0:
                if abs(total_assets - (total_liab + total_equity)) > 0.01 * total_assets:
                    findings.append("Balance Sheet: Assets ≠ Liabilities + Equity")

            # Total Investments should not exceed Total Assets
            total_inv = bs.get('Total Investments', 0)
            if total_inv > total_assets:
                findings.append("Balance Sheet: Total Investments exceeds Total Assets")

        return (len(findings) == 0, findings)

    def check_reasonableness(self, company: str, year: int, data: Dict) -> Tuple[bool, List[str]]:
        """
        Check if values are within reasonable ranges for insurance companies.

        Returns:
            (passed: bool, findings: List[str])
        """
        findings = []

        # Check ratio ranges
        ratios = data.get('ratios', {})

        # Combined ratio should be 80-120% for healthy insurers
        combined = ratios.get('Combined Ratio (%)', 0)
        if combined < 0 or combined > 200:
            findings.append(f"Ratios: Combined ratio {combined}% outside typical range (80-120%)")

        # Loss ratio 30-80% is typical
        loss_ratio = ratios.get('Loss Ratio (%)', 0)
        if loss_ratio < 0 or loss_ratio > 100:
            findings.append(f"Ratios: Loss ratio {loss_ratio}% implausible")

        # Expense ratio 15-40% is typical
        expense_ratio = ratios.get('Expense Ratio (%)', 0)
        if expense_ratio < 0 or expense_ratio > 100:
            findings.append(f"Ratios: Expense ratio {expense_ratio}% implausible")

        # ROE 5-15% is typical for insurance
        roe = ratios.get('ROE (%)', 0)
        if roe < -50 or roe > 100:
            findings.append(f"Ratios: ROE {roe}% extreme (typical: 5-15%)")

        # Check balance sheet reasonableness
        bs = data.get('balance_sheet', {})
        total_assets = bs.get('Total Assets', 0)
        total_inv = bs.get('Total Investments', 0)

        if total_assets > 0 and total_inv > 0:
            inv_ratio = total_inv / total_assets
            if inv_ratio < 0.5 or inv_ratio > 1.0:
                findings.append(f"Balance: Investments/Assets ratio {inv_ratio:.1%} unusual")

        # Check if premiums are reasonable
        inc = data.get('income_statement', {})
        premiums = inc.get('Net Premiums Earned', 0)
        losses = inc.get('Losses and LAE', 0)

        if premiums > 0 and losses > 0:
            loss_ratio = losses / premiums
            if loss_ratio > 1.5:  # Loss ratio > 150% is concerning
                findings.append(f"Income: Loss ratio {loss_ratio:.1%} very high")

        return (len(findings) == 0, findings)

    def check_completeness(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Verify all required fields are present and non-null.

        Returns:
            (passed: bool, findings: List[str])
        """
        findings = []

        required_income = [
            'Net Premiums Earned',
            'Total Revenues',
            'Total Expenses',
            'Net Income'
        ]

        required_balance = [
            'Total Assets',
            'Total Liabilities',
            'Total Equity'
        ]

        inc = data.get('income_statement', {})
        for field in required_income:
            val = inc.get(field)
            if val is None or val == '':
                findings.append(f"Income: Missing required field '{field}'")

        bs = data.get('balance_sheet', {})
        for field in required_balance:
            val = bs.get(field)
            if val is None or val == '':
                findings.append(f"Balance: Missing required field '{field}'")

        return (len(findings) == 0, findings)

    def check_trend_analysis(self, company: str, year: int) -> Tuple[bool, List[str]]:
        """
        Check year-over-year trends for consistency.

        Returns:
            (passed: bool, findings: List[str])
        """
        findings = []

        try:
            # Get current year data
            current = self.data_loader.get_company_snapshot(company, year)
            if not current:
                return (True, [])

            # Get prior year data
            prior_year = year - 1
            prior = self.data_loader.get_company_snapshot(company, prior_year)
            if not prior:
                return (True, ["Note: No prior year data for trend comparison"])

            # Compare key metrics
            curr_assets = current['financial_data']['balance_sheet'].get('Total Assets', 0)
            prior_assets = prior['financial_data']['balance_sheet'].get('Total Assets', 0)

            if curr_assets > 0 and prior_assets > 0:
                change = (curr_assets - prior_assets) / prior_assets
                if change < -0.3:  # More than 30% decrease
                    findings.append(f"Trend: Assets decreased {change:.1%} YoY (unusual)")
                if change > 1.0:  # More than 100% increase
                    findings.append(f"Trend: Assets increased {change:.1%} YoY (verify)")

            # Check premium trend
            curr_prem = current['financial_data']['income_statement'].get('Net Premiums Earned', 0)
            prior_prem = prior['financial_data']['income_statement'].get('Net Premiums Earned', 0)

            if curr_prem > 0 and prior_prem > 0:
                change = (curr_prem - prior_prem) / prior_prem
                if change > 0.5 or change < -0.5:
                    findings.append(f"Trend: Premiums changed {change:.1%} YoY (verify growth)")

        except Exception as e:
            findings.append(f"Trend analysis error: {str(e)}")

        return (len(findings) == 0, findings)

    def check_data_integrity(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Check data types, formats, and values.

        Returns:
            (passed: bool, findings: List[str])
        """
        findings = []

        def check_numeric(section: str, field: str, value: Any):
            """Verify value is numeric."""
            if value is None or value == '':
                return
            try:
                num = float(value)
                if num < 0:
                    findings.append(f"{section}: {field} is negative ({num})")
            except (ValueError, TypeError):
                findings.append(f"{section}: {field} is not numeric ({value})")

        # Check income statement
        inc = data.get('income_statement', {})
        for field, value in inc.items():
            check_numeric('Income', field, value)

        # Check balance sheet
        bs = data.get('balance_sheet', {})
        for field, value in bs.items():
            check_numeric('Balance', field, value)

        # Check ratios
        ratios = data.get('ratios', {})
        for field, value in ratios.items():
            check_numeric('Ratios', field, value)

        return (len(findings) == 0, findings)

    # ═══════════════════════════════════════════════════════════════
    # VALIDATION ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════

    def validate(self, company: str, year: int, data: Dict) -> Dict[str, Any]:
        """
        Run all validation checks on financial data.

        Args:
            company: Company name
            year: Financial year
            data: {income_statement, balance_sheet, ratios}

        Returns:
            {
                audit_id,
                status,
                passed,
                confidence,
                checks: [
                    {name, passed, findings},
                    ...
                ],
                summary,
                timestamp
            }
        """
        audit_id = self._create_audit_id()

        # Run all checks
        checks = []

        # 1. Mathematical Consistency
        passed, findings = self.check_mathematical_consistency(data)
        checks.append({
            'name': 'Mathematical Consistency',
            'category': 'calculations',
            'passed': passed,
            'findings': findings
        })

        # 2. Reasonableness
        passed, findings = self.check_reasonableness(company, year, data)
        checks.append({
            'name': 'Reasonableness',
            'category': 'ranges',
            'passed': passed,
            'findings': findings
        })

        # 3. Completeness
        passed, findings = self.check_completeness(data)
        checks.append({
            'name': 'Completeness',
            'category': 'required_fields',
            'passed': passed,
            'findings': findings
        })

        # 4. Trend Analysis
        passed, findings = self.check_trend_analysis(company, year)
        checks.append({
            'name': 'Trend Analysis',
            'category': 'yoy_changes',
            'passed': passed,
            'findings': findings
        })

        # 5. Data Integrity
        passed, findings = self.check_data_integrity(data)
        checks.append({
            'name': 'Data Integrity',
            'category': 'data_types',
            'passed': passed,
            'findings': findings
        })

        # Calculate overall status and confidence
        passed_checks = sum(1 for c in checks if c['passed'])
        total_checks = len(checks)
        confidence = int((passed_checks / total_checks) * 100)
        overall_passed = confidence >= 80

        # Build summary
        summary = f"{passed_checks}/{total_checks} checks passed. "
        if overall_passed:
            summary += "Data is valid."
        else:
            summary += "Data has issues requiring review."

        # Store in audit log
        audit_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'audit_id': audit_id,
            'company': company,
            'year': year,
            'checks_performed': [c['name'] for c in checks],
            'overall_passed': overall_passed,
            'confidence': confidence,
            'by_module': 'auditor'
        }

        self.audit_log[audit_id] = audit_entry
        self._save_audit_log()

        return {
            'audit_id': audit_id,
            'status': 'success',
            'passed': overall_passed,
            'confidence': confidence,
            'checks': checks,
            'summary': summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def get_audit_log(self, audit_id: Optional[str] = None) -> Dict:
        """
        Get audit log entry or entries.

        Args:
            audit_id: Optional specific audit ID

        Returns:
            Single entry or all entries
        """
        if audit_id:
            return self.audit_log.get(audit_id, {})
        return self.audit_log

    def get_company_audit_history(self, company: str) -> List[Dict]:
        """Get all audits for a company."""
        return [
            entry for entry in self.audit_log.values()
            if entry.get('company') == company
        ]


# Global instance
_auditor = None

def get_auditor() -> FinancialAuditor:
    """Get or create global FinancialAuditor instance."""
    global _auditor
    if _auditor is None:
        _auditor = FinancialAuditor()
    return _auditor
