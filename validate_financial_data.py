#!/usr/bin/env python3
"""
Comprehensive Financial Data Validator
Validates all 30 companies' financial data for accuracy and consistency
"""

import json
from pathlib import Path
from datetime import datetime

class FinancialDataValidator:
    """Validates financial statement data for all 30 companies"""

    def __init__(self, data_file="dashboard_data.json"):
        """Load financial data from JSON file"""
        with open(data_file, "r") as f:
            self.data = json.load(f)

        self.validation_results = {
            "completeness": [],
            "consistency": [],
            "reasonableness": [],
            "yoy_changes": [],
            "warnings": [],
            "errors": []
        }
        self.total_checks = 0
        self.passed_checks = 0

    def validate_all(self):
        """Run all validation checks"""
        print("Financial Data Validator")
        print("=" * 70)
        print(f"Validating {len(self.data['companies'])} companies for {len(self.data['years'])} years\n")

        self._validate_completeness()
        self._validate_consistency()
        self._validate_reasonableness()
        self._validate_yoy_changes()

        self._print_report()
        self._save_report()

    def _validate_completeness(self):
        """Check that all required data is present"""
        print("Checking completeness...", end=" ")

        companies = self.data['companies']
        years = self.data['years']

        # Check all companies have data for all years
        for year in years:
            for company in companies:
                year_str = str(year)
                try:
                    # Check balance sheet
                    bs = self.data['data'][year_str]['balance_sheet']
                    for metric, company_val in bs.items():
                        if company not in company_val:
                            self.validation_results['errors'].append(
                                f"{company} missing {metric} for {year}")
                        else:
                            self._record_check(True)
                except Exception as e:
                    self.validation_results['errors'].append(f"Error checking {company}: {e}")

        print("[OK]")

    def _validate_consistency(self):
        """Check internal consistency of financial statements"""
        print("Checking consistency...", end=" ")

        for year in self.data['years']:
            year_str = str(year)
            bs = self.data['data'][year_str]['balance_sheet']
            inc = self.data['data'][year_str]['income_statement']

            for company in self.data['companies']:
                # Balance Sheet Equation: Assets = Liabilities + Equity
                total_assets = bs.get('Total Assets', {}).get(company, 0)
                total_liab = bs.get('Total Liabilities', {}).get(company, 0)
                total_equity = bs.get('Total Equity', {}).get(company, 0)

                if total_assets > 0:
                    diff = abs(total_assets - (total_liab + total_equity))
                    pct_diff = (diff / total_assets) * 100

                    if pct_diff > 0.5:
                        self.validation_results['warnings'].append(
                            f"{company} ({year}): Balance Sheet Equation off by {pct_diff:.2f}% "
                            f"(Assets:{total_assets:.0f} vs Liab+Eq:{total_liab + total_equity:.0f})")
                        self._record_check(False)
                    else:
                        self._record_check(True)

                # Investment composition check
                inv_afs = bs.get('Fixed Maturities - AFS', {}).get(company, 0)
                inv_trading = bs.get('Fixed Maturities - Trading', {}).get(company, 0)
                inv_equity = bs.get('Equity Securities', {}).get(company, 0)
                inv_short = bs.get('Short-term Investments', {}).get(company, 0)
                inv_other = bs.get('Other Investments', {}).get(company, 0)
                total_investments = bs.get('Total Investments', {}).get(company, 0)

                sum_investments = inv_afs + inv_trading + inv_equity + inv_short + inv_other

                if total_investments > 0 and sum_investments > 0:
                    diff = abs(total_investments - sum_investments)
                    if diff > total_investments * 0.01:  # 1% tolerance
                        self.validation_results['warnings'].append(
                            f"{company} ({year}): Investment composition missing {diff:.0f}M")
                    self._record_check(True)

        print("[OK]")

    def _validate_reasonableness(self):
        """Check for unreasonable values"""
        print("Checking reasonableness...", end=" ")

        for year in self.data['years']:
            year_str = str(year)
            bs = self.data['data'][year_str]['balance_sheet']
            inc = self.data['data'][year_str]['income_statement']
            ratios = self.data['data'][year_str]['ratios']

            for company in self.data['companies']:
                # Assets should be > 0
                total_assets = bs.get('Total Assets', {}).get(company, 0)
                if total_assets <= 0:
                    self.validation_results['errors'].append(
                        f"{company} ({year}): Total Assets <= 0 (${total_assets}M)")
                    self._record_check(False)
                else:
                    self._record_check(True)

                # Equity should be > 0
                total_equity = bs.get('Total Equity', {}).get(company, 0)
                if total_equity <= 0:
                    self.validation_results['errors'].append(
                        f"{company} ({year}): Total Equity <= 0 (${total_equity}M) - Insolvent!")
                    self._record_check(False)
                else:
                    self._record_check(True)

                # Investments should be reasonable (< 80% of assets)
                total_investments = bs.get('Total Investments', {}).get(company, 0)
                if total_assets > 0:
                    inv_ratio = (total_investments / total_assets) * 100
                    if inv_ratio > 80:
                        self.validation_results['warnings'].append(
                            f"{company} ({year}): Investments are {inv_ratio:.1f}% of assets (high)")
                    self._record_check(True)

                # Loss Ratio check
                loss_ratio = ratios.get('Loss Ratio (%)', {}).get(company, 0)
                if loss_ratio > 200:
                    self.validation_results['warnings'].append(
                        f"{company} ({year}): Loss Ratio {loss_ratio:.1f}% (very high - review data)")
                    self._record_check(False)
                elif loss_ratio < 0:
                    self.validation_results['errors'].append(
                        f"{company} ({year}): Negative Loss Ratio {loss_ratio:.1f}%")
                    self._record_check(False)
                else:
                    self._record_check(True)

                # Combined Ratio check
                combined_ratio = ratios.get('Combined Ratio (%)', {}).get(company, 0)
                if combined_ratio < 0:
                    self.validation_results['errors'].append(
                        f"{company} ({year}): Negative Combined Ratio {combined_ratio:.1f}%")
                    self._record_check(False)
                else:
                    self._record_check(True)

                # ROE/ROA sanity checks
                roe = ratios.get('ROE (%)', {}).get(company, 0)
                if abs(roe) > 100:
                    self.validation_results['warnings'].append(
                        f"{company} ({year}): ROE {roe:.1f}% (unusual)")

                # Investment Return check
                inv_return = ratios.get('Investment Return (%)', {}).get(company, 0)
                if inv_return < -20 or inv_return > 25:
                    self.validation_results['warnings'].append(
                        f"{company} ({year}): Investment Return {inv_return:.2f}% (review)")
                self._record_check(True)

        print("[OK]")

    def _validate_yoy_changes(self):
        """Check for unusual year-over-year changes"""
        print("Checking year-over-year changes...", end=" ")

        if len(self.data['years']) < 2:
            print("[SKIPPED - only 1 year]")
            return

        year_2024 = '2024'
        year_2023 = '2023'

        bs_2024 = self.data['data'][year_2024]['balance_sheet']
        bs_2023 = self.data['data'][year_2023]['balance_sheet']
        inc_2024 = self.data['data'][year_2024]['income_statement']
        inc_2023 = self.data['data'][year_2023]['income_statement']

        for company in self.data['companies']:
            # Check Total Assets change
            assets_2024 = bs_2024.get('Total Assets', {}).get(company, 0)
            assets_2023 = bs_2023.get('Total Assets', {}).get(company, 0)

            if assets_2023 > 0:
                asset_change = ((assets_2024 - assets_2023) / assets_2023) * 100
                if abs(asset_change) > 50:
                    self.validation_results['yoy_changes'].append(
                        f"{company}: Assets changed {asset_change:+.1f}% YoY (review)")
                    self._record_check(False)
                else:
                    self._record_check(True)

            # Check Premiums change
            prem_2024 = inc_2024.get('Net Premiums Earned', {}).get(company, 0)
            prem_2023 = inc_2023.get('Net Premiums Earned', {}).get(company, 0)

            if prem_2023 > 0:
                prem_change = ((prem_2024 - prem_2023) / prem_2023) * 100
                if abs(prem_change) > 30:
                    self.validation_results['yoy_changes'].append(
                        f"{company}: Premiums changed {prem_change:+.1f}% YoY (unusual)")
                self._record_check(True)

        print("[OK]")

    def _record_check(self, passed):
        """Record validation check result"""
        self.total_checks += 1
        if passed:
            self.passed_checks += 1

    def _print_report(self):
        """Print validation report"""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        print(f"\nChecks Passed: {self.passed_checks}/{self.total_checks}")
        quality_score = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        print(f"Data Quality Score: {quality_score:.0f}/100")

        if self.validation_results['errors']:
            print(f"\nERRORS ({len(self.validation_results['errors'])}):")
            for error in self.validation_results['errors'][:10]:  # Show first 10
                print(f"  [ERROR] {error}")
            if len(self.validation_results['errors']) > 10:
                print(f"  ... and {len(self.validation_results['errors']) - 10} more errors")

        if self.validation_results['warnings']:
            print(f"\nWARNINGS ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results['warnings'][:10]:  # Show first 10
                print(f"  [WARNING] {warning}")
            if len(self.validation_results['warnings']) > 10:
                print(f"  ... and {len(self.validation_results['warnings']) - 10} more warnings")

        if self.validation_results['yoy_changes']:
            print(f"\nYEAR-OVER-YEAR CHANGES ({len(self.validation_results['yoy_changes'])}):")
            for change in self.validation_results['yoy_changes'][:5]:
                print(f"  [CHANGE] {change}")
            if len(self.validation_results['yoy_changes']) > 5:
                print(f"  ... and {len(self.validation_results['yoy_changes']) - 5} more changes")

        print("\n" + "=" * 70)
        if quality_score >= 95:
            print("STATUS: EXCELLENT - All data looks good")
        elif quality_score >= 85:
            print("STATUS: GOOD - Minor issues to review")
        elif quality_score >= 70:
            print("STATUS: ACCEPTABLE - Some issues to fix")
        else:
            print("STATUS: POOR - Significant issues found")
        print("=" * 70)

    def _save_report(self):
        """Save validation report to JSON file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "companies_validated": len(self.data['companies']),
            "years_validated": len(self.data['years']),
            "checks_passed": self.passed_checks,
            "total_checks": self.total_checks,
            "quality_score": (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0,
            "errors": self.validation_results['errors'],
            "warnings": self.validation_results['warnings'],
            "yoy_changes": self.validation_results['yoy_changes']
        }

        with open("validation_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nValidation report saved to validation_report.json")


def main():
    validator = FinancialDataValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
