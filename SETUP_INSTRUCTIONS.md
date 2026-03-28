# BMA Filings System - Setup & Usage

## Status: ✅ FULLY OPERATIONAL

All components of Phase 4 & 5 (Admin Interface + CLI) have been successfully implemented and tested.

---

## Quick Start

### 1. Create .env File

Create a `.env` file in the project root with your Anthropic API key:

```bash
cp .env.example .env
# Edit .env and replace the placeholder with your actual API key
```

Get your API key from: https://console.anthropic.com

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Server

**Option A: Default port (8080)**
```bash
python approve.py
```

**Option B: Custom port**
```bash
SERVER_PORT=5000 python approve.py
```

Server will start and print:
```
BMA Review Server running at http://localhost:8080
  Dashboard:    http://localhost:8080/dashboard.html
  Admin Review: http://localhost:8080/admin_review.html
```

### 4. Access the Admin Interface

Open browser to: `http://localhost:8080/admin_review.html`

---

## Features

### Admin Interface Tabs

1. **Income Statement** - View and edit income data
2. **Balance Sheet** - View and edit balance sheet data
3. **Ratios** - View and edit financial ratios
4. **Bot Queries** - Ask AI questions about companies
5. **Audit Status** - Run validation checks
6. **FCR Upload** - Upload supporting documents

### CLI Interface

```bash
# Query bot about a company
python omniscient_cli.py query --company "Arch Reinsurance" --question "What are the risks?"

# Deep analysis
python omniscient_cli.py analyze --company "Aspen Bermuda" --metrics financial risk

# Compare companies
python omniscient_cli.py compare --companies "Arch" "Aspen" "AXIS"

# Find companies matching criteria
python omniscient_cli.py search --criteria "high leverage"

# Risk assessment
python omniscient_cli.py risks --company "Markel Bermuda"

# Find investment opportunities
python omniscient_cli.py opportunities

# List all companies
python omniscient_cli.py list
```

---

## API Endpoints

### Data Access
- `GET /api/reviews` - Get reviewed financials

### Bot Services
- `POST /api/bot/query` - Ask bot a question
- `POST /api/bot/analyze` - Get deep analysis
- `POST /api/bot/compare` - Compare companies

### Auditor Services
- `POST /api/auditor/validate` - Validate financial data
- `GET /api/auditor/logs` - Get audit trail

### Document Services
- `POST /api/fcr/upload` - Upload FCR document
- `GET /pdfs/*` - Access PDF files

### Administrative
- `POST /api/save` - Save draft
- `POST /api/approve` - Approve and publish

---

## Testing the System

### 1. Test Admin Interface
```bash
# Browser: http://localhost:8080/admin_review.html
# Select a company and year
# Try each tab to verify functionality
```

### 2. Test Bot Endpoint (requires API key)
```bash
curl -X POST http://localhost:8080/api/bot/query \
  -H "Content-Type: application/json" \
  -d '{"company":"Arch Reinsurance","question":"What are the main risks?"}'
```

### 3. Test Auditor Endpoint
```bash
curl -X POST http://localhost:8080/api/auditor/validate \
  -H "Content-Type: application/json" \
  -d '{
    "company":"Arch Reinsurance",
    "year":2024,
    "data":{
      "income_statement":{"premiums":1000000},
      "balance_sheet":{"assets":5000000},
      "ratios":{"combined_ratio":0.90}
    }
  }'
```

### 4. Test FCR Upload
```bash
curl -X POST http://localhost:8080/api/fcr/upload \
  -H "Content-Type: application/json" \
  -d '{"company":"Arch","year":2024}'
```

### 5. Test PDF Access
```bash
# Browser: http://localhost:8080/pdfs/2025-07-02-11-38-56-Arch-Reinsurance-Ltd.---2024-Financial-Statement---Class-4.pdf
# Or curl: curl -I http://localhost:8080/pdfs/[filename]
```

---

## Configuration

### Environment Variables

Create `.env` file with:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE

# Optional
BOT_MODEL=claude-haiku-4-5-20251001          # AI model to use
BOT_MAX_TOKENS=2000                          # Max response length
SERVER_PORT=8080                             # Server port
SERVER_HOST=localhost                        # Server host
```

### Data Files

- `data/dashboard_data.json` - Company financial data (40 companies, 2023-2024)
- `data/company_snapshots.json` - Snapshot format for bot analysis (auto-generated)
- `data/reviewed_financials.json` - User-submitted reviews and approvals
- `data/audit_log.json` - Audit trail for all operations

---

## Troubleshooting

### Bot queries returning "ANTHROPIC_API_KEY not set"
**Solution**: Create `.env` file with your Anthropic API key

### API endpoints returning 404
**Solution**: Make sure you're running `python approve.py` not `python -m http.server`

### PDFs not loading in browser
**Solution**: Verify `/pdfs/` directory exists and contains PDF files

### Server won't start
1. Check if port 8080 is already in use: `netstat -ano | grep 8080`
2. Try a different port: `SERVER_PORT=5000 python approve.py`
3. Ensure all dependencies installed: `pip install -r requirements.txt`

### Audit validation failing
1. Ensure all required financial statement fields are populated
2. Check that ratio values are within reasonable ranges
3. Review detailed findings in validation response

---

## File Structure

```
bma-filings/
├── approve.py                    # Main API server
├── omniscient_bot.py            # AI analysis engine
├── omniscient_cli.py            # Command-line interface
├── auditor.py                   # Validation engine
├── data_loader.py               # Data management
├── admin_review.html            # Admin interface
├── dashboard.html               # Dashboard view
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── pdfs/                        # PDF storage
└── data/
    ├── dashboard_data.json      # Core financial data
    ├── company_snapshots.json   # Snapshots for bot
    ├── reviewed_financials.json # User reviews
    └── audit_log.json           # Audit trail
```

---

## Module Descriptions

### omniscient_bot.py (400 lines)
- Claude Haiku powered AI analysis
- Functions: query, analyze_company, compare_companies, search_companies, identify_opportunities, risk_assessment
- Multi-turn conversation support
- Audit trail logging

### auditor.py (350 lines)
- Financial data validation
- 5 validation checks: consistency, reasonableness, completeness, trends, integrity
- Confidence scoring
- Detailed findings reporting

### data_loader.py (200 lines)
- Loads and manages company financial snapshots
- Query methods for accessing company data
- Year-over-year comparisons

### approve.py (432 lines)
- HTTP server with custom request handlers
- 12 API endpoints for bot, auditor, and admin functions
- Static file serving
- Git integration for approvals

### omniscient_cli.py (280 lines)
- Command-line interface to bot
- 7 commands: query, analyze, compare, search, risks, opportunities, list
- Pretty-printed results with audit IDs

---

## Support

For issues:
1. Verify `.env` file is configured correctly
2. Check `data/audit_log.json` for operation logs
3. Review server logs for errors
4. Ensure all Python dependencies are installed

---

**Last Updated:** March 20, 2026
**System Status:** Fully Operational ✅
