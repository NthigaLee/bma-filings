#!/usr/bin/env python3
"""
Data Loader Module
Loads and manages company financial snapshots from dashboard_data.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

REPO_ROOT = Path(__file__).parent
DASHBOARD_PATH = REPO_ROOT / 'dashboard_data.json'
SNAPSHOTS_PATH = REPO_ROOT / 'data' / 'company_snapshots.json'


class DataLoader:
    """Loads and manages company financial snapshots."""

    def __init__(self):
        self.snapshots = {}
        self.companies = []
        self.years = []
        self.dashboard_data = {}
        self._load()

    def _load(self):
        """Load dashboard data and initialize snapshots."""
        try:
            with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
                self.dashboard_data = json.load(f)

            self.companies = self.dashboard_data.get('companies', [])
            self.years = self.dashboard_data.get('years', [])

            # Try to load existing snapshots, or generate from dashboard
            if SNAPSHOTS_PATH.exists():
                with open(SNAPSHOTS_PATH, 'r', encoding='utf-8') as f:
                    self.snapshots = json.load(f)
            else:
                self._generate_snapshots()
                self._save_snapshots()

        except Exception as e:
            print(f"Error loading data: {e}")
            self.companies = []
            self.years = []
            self.dashboard_data = {}
            self.snapshots = {}

    def _generate_snapshots(self):
        """Generate company snapshots from dashboard data."""
        data = self.dashboard_data.get('data', {})

        for company in self.companies:
            self.snapshots[company] = {}

            for year in self.years:
                year_str = str(year)
                year_data = data.get(year_str, {})

                # Build snapshot for this company/year
                snapshot = {
                    'year': year,
                    'financial_data': {
                        'income_statement': {},
                        'balance_sheet': {},
                        'ratios': {}
                    },
                    'metadata': {
                        'last_updated': None,
                        'data_quality': 'complete'
                    }
                }

                # Extract financial values from dashboard
                for section in ('income_statement', 'balance_sheet', 'ratios'):
                    section_data = year_data.get(section, {})
                    for field, companies_data in section_data.items():
                        if isinstance(companies_data, dict) and company in companies_data:
                            snapshot['financial_data'][section][field] = companies_data[company]

                self.snapshots[company][year_str] = snapshot

    def _save_snapshots(self):
        """Save snapshots to file."""
        SNAPSHOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SNAPSHOTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots, f, indent=2)

    def get_company_snapshot(self, company: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Get snapshot for a company, optionally filtered by year.

        Args:
            company: Company name
            year: Optional year (defaults to latest)

        Returns:
            Snapshot dict or None
        """
        if company not in self.snapshots:
            return None

        if year is None:
            # Return latest year
            year = max(self.years) if self.years else None

        year_str = str(year) if year else None
        if year_str and year_str in self.snapshots[company]:
            return self.snapshots[company][year_str]

        return None

    def get_all_companies(self) -> List[str]:
        """Get list of all companies."""
        return self.companies.copy()

    def get_financial_value(
        self,
        company: str,
        year: int,
        section: str,
        field: str
    ) -> Optional[float]:
        """
        Get a specific financial value.

        Args:
            company: Company name
            year: Financial year
            section: 'income_statement', 'balance_sheet', or 'ratios'
            field: Field name (e.g., 'Total Assets')

        Returns:
            Numeric value or None
        """
        snapshot = self.get_company_snapshot(company, year)
        if not snapshot:
            return None

        return snapshot['financial_data'][section].get(field)

    def search_companies(self, criteria: str) -> List[str]:
        """
        Search companies by name.

        Args:
            criteria: Search string (case-insensitive)

        Returns:
            List of matching company names
        """
        criteria_lower = criteria.lower()
        return [c for c in self.companies if criteria_lower in c.lower()]

    def get_companies_by_metric(
        self,
        metric: str,
        year: int,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get companies filtered by a financial metric.

        Args:
            metric: Field name (e.g., 'Total Assets')
            year: Financial year
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            List of dicts: {company, value, ratio_to_median}
        """
        results = []
        values = []

        # Find values for all companies
        for company in self.companies:
            # Try all sections to find the metric
            for section in ('income_statement', 'balance_sheet', 'ratios'):
                val = self.get_financial_value(company, year, section, metric)
                if val is not None:
                    results.append({'company': company, 'value': val})
                    values.append(val)
                    break

        # Filter by range if specified
        if min_val is not None or max_val is not None:
            results = [
                r for r in results
                if (min_val is None or r['value'] >= min_val)
                and (max_val is None or r['value'] <= max_val)
            ]

        # Calculate median for ratio
        if values:
            median = sorted(values)[len(values) // 2]
            for r in results:
                r['ratio_to_median'] = r['value'] / median if median != 0 else 1.0

        return sorted(results, key=lambda r: r['value'], reverse=True)

    def get_years(self) -> List[int]:
        """Get available years."""
        return self.years.copy()

    def compare_company_years(self, company: str) -> Dict[int, Dict]:
        """
        Get company data across all years for comparison.

        Args:
            company: Company name

        Returns:
            Dict mapping year → snapshot
        """
        if company not in self.snapshots:
            return {}

        return {
            int(year): snapshot
            for year, snapshot in self.snapshots[company].items()
        }

    def reload(self):
        """Reload data from files."""
        self._load()


# Global instance
_loader = None

def get_loader() -> DataLoader:
    """Get or create global DataLoader instance."""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader
