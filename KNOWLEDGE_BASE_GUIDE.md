# Knowledge Base System Guide

## Overview

The BMA system now includes a comprehensive **local knowledge base** that stores all company financial information, statements, ownership structures, and notes. This enables:

- **Faster bot responses** (local lookup instead of API calls)
- **Offline operation** (work without Claude API for data lookups)
- **Cost reduction** (fewer API tokens spent on data retrieval)
- **Better context** (rich company information included in bot analysis)

---

## Knowledge Base Structure

### Main Database
- **Location**: `data/knowledge_base.json`
- **Size**: Comprehensive index of 40 companies
- **Updated**: Automatically when you rebuild

### Individual Company Summaries
- **Location**: `data/company_summaries/`
- **Files**: One JSON file per company (e.g., `arch_reinsurance.json`)
- **Purpose**: Quick access to individual company data

---

## Data Included Per Company

### 1. Company Description
- Business focus and operations
- Geographic presence
- Company type (public/private)

### 2. Ownership Structure
```json
{
  "ownership_type": "Public",
  "domicile": "Bermuda",
  "regulatory_body": "BMA",
  "share_structure": {},
  "primary_shareholders": []
}
```

### 3. Financial Statements (per period)
- **Balance Sheet**
  - Total Assets
  - Total Liabilities
  - Total Equity
  - And all supporting line items

- **Income Statement**
  - Premiums
  - Losses
  - Net Income
  - And all supporting line items

- **Financial Ratios**
  - Combined Ratio
  - Loss Ratio
  - ROE (Return on Equity)
  - Equity Ratio
  - And others

### 4. Financial Notes
- **Balance Sheet Notes**: Solvency analysis
- **Income Statement Notes**: Profitability analysis
- **Risk Factors**: Key risk indicators
- **Accounting Methods**: GAAP standards applied

### 5. Key Metrics
- Latest year combined ratio
- ROE (Return on Equity)
- Equity ratio
- Total assets
- Total equity
- Net income
- Premiums

### 6. Trends
- **Premium Growth**: YoY change in premiums
- **Asset Growth**: YoY change in total assets
- **Equity Growth**: YoY change in equity
- **Ratio Changes**: YoY change in key ratios

---

## Building the Knowledge Base

### Initial Build
```bash
python knowledge_base.py build
```

This:
1. Loads `dashboard_data.json`
2. Extracts financial data for all companies
3. Generates company descriptions, notes, and metrics
4. Saves comprehensive `knowledge_base.json`
5. Creates individual company summary files

### Rebuild (when data updates)
```bash
python knowledge_base.py build
```

---

## Using the Knowledge Base

### With the Omniscient Bot

The bot automatically uses the knowledge base when available:

```python
from omniscient_bot import get_bot

bot = get_bot()

# This query uses knowledge base data
result = bot.query("Arch Reinsurance", "What is the company's ownership structure?", 2024)
print(result['analysis'])
```

The bot will:
1. Check knowledge base first (instant)
2. Use KB data if available
3. Fall back to live data if KB missing
4. Include `[Source: Knowledge Base]` in response

### Via CLI

```bash
python omniscient_cli.py query --company "Arch Reinsurance" --question "What are the key metrics?"
```

### Direct Access

```python
from knowledge_base import get_company_kb, search_kb

# Get specific company
arch_kb = get_company_kb("Arch Reinsurance")

# Search for companies
results = search_kb("Bermuda", field="ownership")
print(results)
```

---

## Knowledge Base Functions

### Build & Save
```python
from knowledge_base import build_knowledge_base, save_knowledge_base

kb = build_knowledge_base()
save_knowledge_base(kb)
```

### Query
```python
from knowledge_base import get_company_kb, search_kb

# Get company KB entry
company_kb = get_company_kb("Arch Reinsurance")

# Search KB
results = search_kb("Bermuda")

# Get summary stats
from knowledge_base import get_kb_summary
stats = get_kb_summary()
```

### CLI Commands

**Build knowledge base:**
```bash
python knowledge_base.py build
```

**Search for companies:**
```bash
python knowledge_base.py search "Bermuda"
```

**View KB info:**
```bash
python knowledge_base.py info
```

---

## What Each Company Entry Contains

Example for Arch Reinsurance:

```json
{
  "name": "Arch Reinsurance",
  "description": "Global reinsurance company specializing in catastrophe and specialty reinsurance.",
  "ownership": {
    "ownership_type": "Public",
    "domicile": "Bermuda",
    "regulatory_body": "BMA",
    "share_structure": {},
    "primary_shareholders": []
  },
  "key_metrics": {
    "combined_ratio": 0.92,
    "roe": 0.12,
    "equity_ratio": 0.31,
    "total_assets": 70700000,
    "total_equity": 21900000,
    "net_income": 2300000,
    "premiums": 15000000
  },
  "trends": {
    "premium_growth": 5.2,
    "asset_growth": 3.1,
    "equity_growth": 4.5,
    "ratio_changes": {}
  },
  "periods": {
    "2024": {
      "balance_sheet": { ... },
      "income_statement": { ... },
      "ratios": { ... },
      "notes": {
        "balance_sheet_notes": "...",
        "income_statement_notes": "...",
        "risk_factors": "..."
      }
    },
    "2023": { ... }
  },
  "last_updated": "2026-03-20T02:15:00+00:00"
}
```

---

## Integration with Auditor

The auditor also benefits from the knowledge base:

```python
from auditor import get_auditor
from knowledge_base import get_company_kb

auditor = get_auditor()

# Can reference KB data for validation
company_kb = get_company_kb("Arch Reinsurance")
historical_ratios = company_kb['periods']['2023']['ratios']

# Use for trend validation
result = auditor.validate("Arch Reinsurance", 2024, financial_data)
```

---

## Performance Benefits

### Without Knowledge Base
- Bot query: 1-3 seconds (API call + processing)
- Each query costs API tokens

### With Knowledge Base
- Bot query: <100ms (local lookup + processing)
- No API calls for data retrieval
- Same quality responses with local data

---

## Data Refresh Strategy

### When to Rebuild
1. **After major data updates**: New financial statements received
2. **Quarterly**: Regular data refresh
3. **After corrections**: When submitted data is corrected

### Automated Refresh
Consider adding to your workflow:
```bash
# After saving new financials
python knowledge_base.py build
git add data/knowledge_base.json data/company_summaries/
git commit -m "Update knowledge base with latest data"
```

---

## Future Enhancements

Potential additions to the knowledge base:

1. **Embeddings**: Vector embeddings for semantic search
2. **News & Events**: Company-specific news timeline
3. **Regulatory Changes**: BMA regulation updates
4. **Peer Comparisons**: Industry benchmarks
5. **Full-Text Search**: Advanced search capabilities
6. **Historical Archive**: Multi-year snapshots
7. **API Gateway**: REST API for KB queries

---

## Troubleshooting

### Knowledge Base Not Used
**Problem**: Bot shows `[Source: Live Data Loader]`

**Solution**: Ensure KB is built
```bash
python knowledge_base.py build
```

### Missing Company Data
**Problem**: Company not in KB

**Solution**: Rebuild KB after adding new company
```bash
python knowledge_base.py build
```

### Stale Data
**Problem**: KB data is outdated

**Solution**: Rebuild periodically
```bash
python knowledge_base.py build
```

---

## Summary

The knowledge base system provides:

✓ Complete financial information per company per period
✓ Company descriptions and ownership structures
✓ Financial statements and detailed notes
✓ Key metrics and trends
✓ Fast local lookups (no API calls)
✓ Offline operation capability
✓ Cost reduction for bot queries
✓ Enhanced context for better analysis

All data is automatically indexed and searchable, making the bots more capable and efficient.
