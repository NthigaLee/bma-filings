#!/usr/bin/env python3
"""
Omniscient Bot Module
AI-powered company analysis using Claude Opus
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from data_loader import get_loader

# Try to import knowledge base module
try:
    from knowledge_base import load_knowledge_base, get_company_kb
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False
    get_company_kb = None

# Load .env file if it exists (ensure API key is available)
_env_file = Path(__file__).parent / '.env'
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key == 'ANTHROPIC_API_KEY' and not os.environ.get(key):
                    os.environ[key] = value

REPO_ROOT = Path(__file__).parent
AUDIT_LOG_PATH = REPO_ROOT / 'data' / 'audit_log.json'


class OmniscientBot:
    """AI-powered company analyzer using Claude Opus."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize bot with Claude API key.

        Args:
            api_key: Optional API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        if Anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.data_loader = get_loader()
        self.conversations = {}  # Store multi-turn context by session ID

    def _get_company_from_kb(self, company: str) -> Optional[Dict[str, Any]]:
        """Try to get company information from knowledge base."""
        if KB_AVAILABLE and get_company_kb:
            return get_company_kb(company)
        return None

    def _create_audit_id(self) -> str:
        """Generate unique audit ID."""
        return str(uuid.uuid4())[:8]

    def _log_to_audit(self, audit_id: str, company: str, year: int,
                     analysis: str, confidence: int, query_type: str):
        """Log operation to audit log."""
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        audit_log = {}
        if AUDIT_LOG_PATH.exists():
            with open(AUDIT_LOG_PATH, 'r') as f:
                audit_log = json.load(f)

        audit_log[audit_id] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'company': company,
            'year': year,
            'query_type': query_type,
            'analysis_preview': analysis[:200] + ('...' if len(analysis) > 200 else ''),
            'confidence': confidence,
            'by_module': 'omniscient_bot'
        }

        with open(AUDIT_LOG_PATH, 'w') as f:
            json.dump(audit_log, f, indent=2)

    def _get_company_context(self, company: str, year: int) -> str:
        """Build context string with company financial data from KB or live data."""
        # Try knowledge base first (faster, no API calls)
        kb_entry = self._get_company_from_kb(company)
        if kb_entry and str(year) in kb_entry.get('periods', {}):
            year_data = kb_entry['periods'][str(year)]
            lines = [f"Company: {company}, Year: {year}"]
            lines.append(f"Description: {kb_entry.get('description', '')}")
            lines.append(f"Ownership: {kb_entry.get('ownership', {}).get('ownership_type', 'Unknown')}")

            lines.append("\nBalance Sheet (USD thousands):")
            bs = year_data.get('balance_sheet', {})
            for field, value in bs.items():
                if value:
                    lines.append(f"  {field}: {value:,.0f}")

            lines.append("\nIncome Statement (USD thousands):")
            inc = year_data.get('income_statement', {})
            for field, value in inc.items():
                if value:
                    lines.append(f"  {field}: {value:,.0f}")

            lines.append("\nFinancial Ratios:")
            ratios = year_data.get('ratios', {})
            for field, value in ratios.items():
                if value:
                    lines.append(f"  {field}: {value:.2f}")

            lines.append("\nNotes:")
            notes = year_data.get('notes', {})
            if notes.get('balance_sheet_notes'):
                lines.append(f"  Balance Sheet: {notes['balance_sheet_notes']}")
            if notes.get('income_statement_notes'):
                lines.append(f"  Income Statement: {notes['income_statement_notes']}")
            if notes.get('risk_factors'):
                lines.append(f"  Risk Factors: {notes['risk_factors']}")

            lines.append("\n[Source: Knowledge Base]")
            return "\n".join(lines)

        # Fallback to live data loader
        snapshot = self.data_loader.get_company_snapshot(company, year)
        if not snapshot:
            return f"No data found for {company} in {year}"

        # Build context from financial data
        lines = [f"Company: {company}, Year: {year}"]
        lines.append("\nBalance Sheet (USD thousands):")

        bs = snapshot['financial_data'].get('balance_sheet', {})
        for field, value in bs.items():
            if value:
                lines.append(f"  {field}: {value:,.0f}")

        lines.append("\nIncome Statement (USD thousands):")
        inc = snapshot['financial_data'].get('income_statement', {})
        for field, value in inc.items():
            if value:
                lines.append(f"  {field}: {value:,.0f}")

        lines.append("\nFinancial Ratios:")
        ratios = snapshot['financial_data'].get('ratios', {})
        for field, value in ratios.items():
            if value:
                lines.append(f"  {field}: {value:.2f}")

        lines.append("\n[Source: Live Data Loader]")
        return "\n".join(lines)

    def query(self, company: str, question: str, year: Optional[int] = None,
             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask the bot a question about a company.

        Args:
            company: Company name
            question: Question to ask
            year: Optional year (defaults to latest)
            session_id: Optional session for multi-turn conversation

        Returns:
            {status, analysis, confidence, audit_id}
        """
        audit_id = self._create_audit_id()
        year = year or max(self.data_loader.get_years())

        try:
            context = self._get_company_context(company, year)

            # Build conversation history
            messages = []
            if session_id and session_id in self.conversations:
                messages = self.conversations[session_id].copy()

            messages.append({
                'role': 'user',
                'content': f"{context}\n\nQuestion: {question}"
            })

            # Call Claude Opus
            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1000,
                messages=messages
            )

            analysis = response.content[0].text
            confidence = 85  # Default confidence

            # Store conversation if session provided
            if session_id:
                messages.append({'role': 'assistant', 'content': analysis})
                self.conversations[session_id] = messages

            self._log_to_audit(audit_id, company, year, analysis, confidence, 'query')

            return {
                'status': 'success',
                'analysis': analysis,
                'confidence': confidence,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'analysis': str(e),
                'confidence': 0,
                'audit_id': audit_id
            }

    def analyze_company(self, company: str, year: Optional[int] = None,
                       metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform deep analysis of a company.

        Args:
            company: Company name
            year: Optional year
            metrics: List of metrics to analyze (['financial', 'risk', 'growth'])

        Returns:
            {status, analysis, audit_id}
        """
        audit_id = self._create_audit_id()
        year = year or max(self.data_loader.get_years())
        metrics = metrics or ['financial', 'risk']

        try:
            context = self._get_company_context(company, year)

            prompt = f"""{context}

Please provide a comprehensive analysis of {company} covering:
{chr(10).join(f"- {m.capitalize()} analysis" for m in metrics)}

Focus on:
1. Key strengths and weaknesses
2. Trends and changes
3. Risks and opportunities
4. Comparison to industry benchmarks (where possible)

Keep analysis concise but detailed."""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )

            analysis = response.content[0].text

            self._log_to_audit(audit_id, company, year, analysis, 90, 'analyze')

            return {
                'status': 'success',
                'analysis': analysis,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'analysis': str(e),
                'audit_id': audit_id
            }

    def compare_companies(self, companies: List[str], year: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare multiple companies.

        Args:
            companies: List of company names
            year: Optional year

        Returns:
            {status, comparison, audit_id}
        """
        audit_id = self._create_audit_id()
        year = year or max(self.data_loader.get_years())

        try:
            contexts = []
            for company in companies:
                ctx = self._get_company_context(company, year)
                contexts.append(ctx)

            prompt = f"""Compare the following companies for year {year}:

{chr(10).join(f"--- {company} ---{chr(10)}{ctx}" for company, ctx in zip(companies, contexts))}

Please provide:
1. Side-by-side comparison of key metrics
2. Relative strengths and weaknesses
3. Investment perspective (which would you prefer and why?)
4. Risk assessment for each"""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=2000,
                messages=[{'role': 'user', 'content': prompt}]
            )

            comparison = response.content[0].text

            self._log_to_audit(audit_id, ','.join(companies), year, comparison, 85, 'compare')

            return {
                'status': 'success',
                'comparison': comparison,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'comparison': str(e),
                'audit_id': audit_id
            }

    def search_companies(self, criteria: str) -> Dict[str, Any]:
        """
        Search companies by financial criteria.

        Args:
            criteria: Search criteria (e.g., "high equity ratio", "low combined ratio")

        Returns:
            {status, results, audit_id}
        """
        audit_id = self._create_audit_id()

        try:
            # Get all companies and their data
            companies = self.data_loader.get_all_companies()
            year = max(self.data_loader.get_years())

            company_data = []
            for company in companies:
                snapshot = self.data_loader.get_company_snapshot(company, year)
                if snapshot:
                    company_data.append({
                        'company': company,
                        'data': snapshot
                    })

            prompt = f"""Given the following companies' financial data for {year},
find those matching the criteria: "{criteria}"

Companies:
{json.dumps([c['company'] for c in company_data], indent=2)}

For each company, provide:
1. Whether it matches the criteria (yes/no/partially)
2. Key metrics supporting your assessment
3. Relevance score (0-100)

Return results sorted by relevance."""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1000,
                messages=[{'role': 'user', 'content': prompt}]
            )

            results = response.content[0].text

            self._log_to_audit(audit_id, 'multiple', year, results, 75, 'search')

            return {
                'status': 'success',
                'results': results,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'results': str(e),
                'audit_id': audit_id
            }

    def identify_opportunities(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Identify investment opportunities.

        Args:
            filters: Optional filters {metric: value, ...}

        Returns:
            {status, opportunities, audit_id}
        """
        audit_id = self._create_audit_id()
        year = max(self.data_loader.get_years())

        try:
            companies = self.data_loader.get_all_companies()
            prompt = f"""Analyze {len(companies)} insurance/reinsurance companies for {year} and identify:

1. Undervalued companies (good fundamentals, attractive metrics)
2. Growth opportunities (companies with improving trends)
3. Value traps to avoid (appear cheap but have concerning trends)
4. Acquisition targets (strategically interesting)

Consider metrics like:
- Combined ratio (efficiency)
- ROE (profitability)
- Equity ratio (solvency)
- Premium growth

Provide top 5-7 opportunities with reasoning."""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )

            opportunities = response.content[0].text

            self._log_to_audit(audit_id, 'market', year, opportunities, 80, 'opportunities')

            return {
                'status': 'success',
                'opportunities': opportunities,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'opportunities': str(e),
                'audit_id': audit_id
            }

    def risk_assessment(self, company: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform risk assessment for a company.

        Args:
            company: Company name
            year: Optional year

        Returns:
            {status, assessment, risk_level, audit_id}
        """
        audit_id = self._create_audit_id()
        year = year or max(self.data_loader.get_years())

        try:
            context = self._get_company_context(company, year)

            prompt = f"""{context}

Please assess the financial risks for {company}:

1. Solvency Risk: Can they meet obligations?
2. Liquidity Risk: Do they have sufficient liquid assets?
3. Underwriting Risk: Are loss ratios sustainable?
4. Investment Risk: Asset quality and concentration
5. Operational Risk: Business model sustainability
6. Market Risk: Exposure to catastrophic events

For each risk:
- Rate severity (Low/Medium/High/Critical)
- Provide 2-3 specific concerns
- Suggest mitigation factors

Conclude with overall risk level (Safe/Moderate/Risky/High-Risk)"""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )

            assessment = response.content[0].text

            # Determine risk level from response
            risk_level = 'Moderate'
            if 'critical' in assessment.lower():
                risk_level = 'High-Risk'
            elif 'high' in assessment.lower():
                risk_level = 'Risky'
            elif 'safe' in assessment.lower():
                risk_level = 'Safe'

            self._log_to_audit(audit_id, company, year, assessment, 90, 'risk_assessment')

            return {
                'status': 'success',
                'assessment': assessment,
                'risk_level': risk_level,
                'audit_id': audit_id
            }

        except Exception as e:
            return {
                'status': 'error',
                'assessment': str(e),
                'risk_level': 'Unknown',
                'audit_id': audit_id
            }


# Global instance
_bot = None

def get_bot() -> OmniscientBot:
    """Get or create global OmniscientBot instance."""
    global _bot
    if _bot is None:
        _bot = OmniscientBot()
    return _bot
