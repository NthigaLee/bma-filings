# BMA Filings - Enhanced Insurance/Reinsurance Financial Dashboard

A comprehensive interactive dashboard for analyzing financial statements and key performance metrics for major Bermuda-based insurance and reinsurance companies.

## Features

✨ **Interactive Dashboard**
- Real-time company and year filtering (30 companies)
- 10 financial metric charts covering assets, equity, premiums, income, and profitability
- Year-over-year trend analysis with 10 selectable metrics
- Accounting format with comma separators for all numbers
- Comparative analysis table
- Responsive design for desktop and mobile

📊 **Financial Metrics**
- Balance Sheet: Total Assets, Total Equity, Investments, Cash
- Income Statement: Gross Premiums Written, Net Premiums Earned, Total Revenues, Net Income
- Ratios: ROE, ROA, Loss Ratio, Expense Ratio, Combined Ratio, Equity Ratio

🏢 **Companies Covered (30 Total)**
**Original 10:**
1. Arch Reinsurance
2. Ascot Bermuda
3. Aspen Bermuda
4. AXIS Specialty
5. Chubb Tempest Reinsurance
6. Everest Reinsurance Bermuda
7. Hannover Re Bermuda
8. Markel Bermuda
9. Partner Reinsurance Company
10. Renaissance Reinsurance

**Expanded 20:**
11. Endurance Specialty Insurance
12. XL Bermuda
13. AXA XL Reinsurance
14. Validus Reinsurance
15. Somers Re
16. Lancashire Insurance Company
17. Hiscox Insurance Company Bermuda
18. Canopius Reinsurance
19. Conduit Reinsurance
20. Fidelis Insurance Bermuda
21. Fortitude Reinsurance Company
22. Group Ark Insurance
23. Hamilton Re
24. Harrington Re
25. Liberty Specialty Markets Bermuda
26. MS Amlin AG
27. Premia Reinsurance
28. Starr Insurance & Reinsurance
29. Vantage Risk
30. SiriusPoint Bermuda Insurance

📅 **Years Supported**
- 2023
- 2024

## Quick Start

### 🚀 View Dashboard Now
**[→ Open Dashboard Landing Page](index.html)** - Choose between the interactive dashboard and admin console

### Requirements
- Python 3.7+
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/bma-filings.git
   cd bma-filings
   ```

2. **Run the dashboard**
   ```bash
   python run_dashboard.py
   ```

3. **Access the dashboard**
   Open your browser and navigate to:
   ```
   http://localhost:8001/index.html
   ```
   Or directly to the dashboard:
   ```
   http://localhost:8001/dashboard.html
   ```

## Project Structure

```
bma-filings/
├── dashboard.html                          # Main interactive dashboard
├── dashboard_data.json                     # Extracted financial data (2023-2024)
├── run_dashboard.py                        # HTTP server to serve dashboard
├── create_dashboard_data_multi_year.py    # Data extraction script
├── extract_losses_from_pdfs.py            # Loss data extraction from PDFs
├── data/                                   # Excel workbooks
│   ├── BMA_Statements_30_Companies_2024_MILLIONS.xlsx
│   ├── BMA_Statements_30_Companies_2023_MILLIONS.xlsx
│   ├── BMA_Statements_2024_MILLIONS.xlsx (original 10)
│   └── BMA_Statements_2023_MILLIONS.xlsx (original 10)
├── pdfs/                                   # PDF financial statements (250+ files)
│   └── [30 company financial statements for multiple years]
├── docs/                                   # Documentation
│   ├── README_DOCUMENTATION_INDEX.md
│   ├── QUICK_START_v2.md
│   ├── PROJECT_SUMMARY.md
│   ├── ENHANCED_DASHBOARD_GUIDE.md
│   └── ...
└── README.md                               # This file
```

## Dashboard Usage

### Year Filter
Click the year dropdown (top left) to switch between 2023 and 2024 data.

### Company Selection
Check/uncheck company names to include/exclude them from all charts and calculations. Choose from 30 major Bermuda insurance and reinsurance companies.

### Metric Selector (Trend Chart)
Select different metrics from the dropdown to view year-over-year trends for any financial metric or ratio.

### Chart Interactions
- Hover over bars/lines to see exact values
- Charts update dynamically as you adjust filters

### Comparison Table
View detailed metrics side-by-side for all selected companies in the current year.

## Data Sources

Financial data is extracted from:
- **Balance Sheets**: Official financial statements (Excel workbooks)
- **Income Statements**: Company filings (Excel workbooks)
- **Loss Data**: Extracted from 10-K PDF filings (verified from PDFs)

All values are in **USD Millions**.

## Calculated Metrics

### Profitability Ratios
- **ROE (%)** = Net Income / Total Equity
- **ROA (%)** = Net Income / Total Assets

### Underwriting Ratios
- **Loss Ratio (%)** = Losses & LAE / Net Premiums Earned
- **Expense Ratio (%)** = Total Expenses / Net Premiums Earned
- **Combined Ratio (%)** = (Losses + Expenses) / Net Premiums Earned

### Solvency Ratio
- **Equity Ratio (%)** = Total Equity / Total Assets

## Scripts

### `run_dashboard.py`
Starts a local HTTP server on port 8001 to serve the dashboard.

```bash
python run_dashboard.py
```

### `create_dashboard_data_multi_year.py`
Extracts financial data from Excel workbooks and calculates all financial ratios.

```bash
python create_dashboard_data_multi_year.py
```

Reads from:
- `data/BMA_Statements_2024_MILLIONS.xlsx`
- `data/BMA_Statements_2023_MILLIONS.xlsx`

Outputs:
- `dashboard_data.json`

### `extract_losses_from_pdfs.py`
Searches PDF financial statements for loss and LAE data.

```bash
python extract_losses_from_pdfs.py
```

## Technical Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Charts**: Chart.js 3.x
- **Data**: JSON
- **Backend**: Python 3 (SimpleHTTPServer)
- **Data Processing**: openpyxl (Excel), pdfplumber (PDF)

## Browser Compatibility

- ✅ Chrome/Chromium 60+
- ✅ Firefox 55+
- ✅ Safari 11+
- ✅ Edge 79+
- ✅ Mobile browsers (responsive design)

## Color Scheme

- **Primary**: Maroon (#8B1538) - Professional, insurance-industry appropriate
- **Secondary**: White/Light Gray - Clean, readable
- **Charts**: Color-coded by company for easy distinction

## Documentation

For comprehensive documentation, see:
- **[README_DOCUMENTATION_INDEX.md](README_DOCUMENTATION_INDEX.md)** - Navigation guide to all docs
- **[QUICK_START_v2.md](QUICK_START_v2.md)** - 30-second quick start guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[ENHANCED_DASHBOARD_GUIDE.md](ENHANCED_DASHBOARD_GUIDE.md)** - Detailed feature guide
- **[DASHBOARD_LAYOUT_DIAGRAM.txt](DASHBOARD_LAYOUT_DIAGRAM.txt)** - Visual dashboard layout
- **[CHANGELOG_v2.md](CHANGELOG_v2.md)** - Version history and changes

## Troubleshooting

### Dashboard shows no data
1. Ensure `dashboard_data.json` exists in the project root
2. Run `python create_dashboard_data_multi_year.py` to regenerate data
3. Check browser console (F12) for errors
4. Verify Excel files exist in `data/` directory

### Server won't start
1. Check if port 8001 is already in use
2. Try running on a different port by editing `run_dashboard.py`
3. Ensure Python 3 is installed: `python --version`

### Charts are empty after filtering
1. Ensure at least one company and year is selected
2. Try selecting all companies with "Select All" button
3. Refresh the page (Ctrl+R)

## Performance

- Dashboard loads in <1 second
- Chart updates are instant (<100ms)
- Supports up to 10 simultaneous company comparisons
- Optimized for 1366x768 and above (responsive below)

## Future Enhancements

- Additional years (2021, 2022)
- Export to PDF/Excel
- Advanced filtering by metric ranges
- Quarterly data
- Historical trend analysis (3-5 years)
- Peer comparison benchmarking

## License

This project is provided as-is for financial analysis and reporting purposes.

## Contact & Support

For questions or issues, please check the documentation files or contact the project maintainer.

---

**Last Updated**: March 11, 2026
**Version**: 2.1
**Status**: Production Ready ✅
**Features**: Dashboard + Admin Console with PDF Review
