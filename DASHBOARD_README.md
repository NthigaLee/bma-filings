# Insurance/Reinsurance Company Dashboard

## Overview

An interactive, colorful dashboard for comparing financial metrics across 10 major Bermuda-based insurance and reinsurance companies with 2024 financial data.

**All values are in USD Millions**

## Features

### 📊 Dashboard Components

1. **Key Financial Metrics** (Top of page)
   - Total Assets of largest company
   - Average ROE (Return on Equity)
   - Average Loss Ratio
   - Average Combined Ratio

2. **Interactive Company Selection**
   - Select/deselect companies to compare
   - Select All / Clear All buttons
   - Metrics update in real-time

4. **Four Analysis Tabs**
   - **Ratios Tab**: ROE, Loss Ratio, Combined Ratio, Equity Ratio
   - **Assets & Liabilities Tab**: Total Assets, Equity, Liabilities, Loss Reserves
   - **Income & Profitability Tab**: Premiums Earned, Net Income, GPW, Total Revenues
   - **Comparison Table**: Side-by-side financial metrics

5. **Color-Coded Charts**
   - Each metric has its own color for easy identification
   - Responsive bar charts with hover tooltips
   - Real-time updates when companies are selected/deselected

## 10 Companies Included

1. **Arch Reinsurance** - Largest by assets ($40.5B)
2. **Ascot Bermuda** - $6.6B in assets
3. **Aspen Bermuda** - $1.9B in assets
4. **AXIS Specialty** - $4.0B in assets
5. **Chubb Tempest Reinsurance** - Major reinsurer
6. **Everest Reinsurance Bermuda** - Significant player
7. **Hannover Re Bermuda** - International reinsurer
8. **Markel Bermuda** - Diversified operator
9. **Partner Reinsurance** - Specialized reinsurer
10. **Renaissance Reinsurance** - Bermuda-based reinsurer

## How to Run the Dashboard

### Option 1: Using Python Server (Recommended)

1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```bash
   cd "C:\Users\nthig\.claude\projects\bma-filings"
   ```

3. Run the dashboard server:
   ```bash
   python run_dashboard.py
   ```

4. The dashboard will automatically open in your default browser at:
   ```
   http://localhost:8000/dashboard.html
   ```

### Option 2: Using Python's Built-in Server

1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```bash
   cd "C:\Users\nthig\.claude\projects\bma-filings"
   ```

3. Start the server:
   ```bash
   python -m http.server 8000
   ```

4. Open your browser and go to:
   ```
   http://localhost:8000/dashboard.html
   ```

### Option 3: Direct File Opening

Simply double-click `dashboard.html` to open it in your browser (limited interactivity without a server).

## Using the Dashboard

### Step 1: Select Companies
- Check/uncheck companies in the **"Select Companies to Compare"** section
- Use **"Select All"** to compare all companies
- Use **"Clear All"** to deselect and start fresh

### Step 2: View Key Metrics
- The metrics at the top update automatically based on your selection
- See average ratios and top performers

### Step 3: Analyze Charts
- Switch between tabs to see different analyses:
  - **Ratios**: Profitability and operational efficiency metrics
  - **Assets & Liabilities**: Balance sheet composition
  - **Income & Profitability**: Revenue and earnings performance
  - **Comparison Table**: Detailed side-by-side metrics

### Step 4: Interpret the Data

#### Key Ratios Explained:

- **ROE (Return on Equity) %**: Profitability relative to shareholder capital
  - Higher is better (typically 15-25% for insurers)
  - Shows how efficiently the company uses equity capital

- **Loss Ratio %**: Claims and adjustment costs as % of earned premiums
  - Lower is better (industry average ~60%)
  - Under 100% is profitable on underwriting

- **Combined Ratio %**: (Losses + Expenses) / Earned Premiums × 100
  - Below 100% = underwriting profit
  - Above 100% = underwriting loss
  - Industry benchmark: 95-105%

- **Equity Ratio %**: Total Equity / Total Assets
  - Shows capital adequacy and financial leverage
  - Higher indicates stronger balance sheet

#### Balance Sheet Items:

- **Total Assets**: All company resources
- **Total Equity**: Shareholders' ownership stake
- **Total Liabilities**: All obligations
- **Loss Reserves**: Estimated future claim payments

#### Income Statement Items:

- **Gross Premiums Written**: Total premiums before reinsurance
- **Net Premiums Earned**: Core insurance revenue
- **Total Revenues**: Including investment income
- **Net Income**: Bottom-line profitability

#### Cash Flow Items:

- **Operating Cash**: Cash from core insurance business
- **Investing Cash**: Cash from investment activities
- **Financing Cash**: Cash from capital/debt activities

## Dashboard Design Features

### Visual Elements
- **Gradient backgrounds**: Purple to blue color scheme for modern appearance
- **Color-coded metric cards**: Different colors for different metric categories
- **Rounded corners and shadows**: Modern card-based design
- **Responsive layout**: Adapts to different screen sizes
- **Hover effects**: Interactive feedback on buttons and cards

### Interactive Elements
- **Tab switching**: Switch between different analysis views
- **Live updates**: Charts and metrics update in real-time
- **Tooltips**: Hover over chart bars to see exact values
- **Formatted numbers**: Easy-to-read number formatting (commas, decimals)
- **Color-coded values**: Bar charts with color-coded values in the comparison table

## Data Sources

All financial data comes from:
- **Source**: 2024 10-K/Financial Statements filed by each company
- **Unit Conversion**:
  - Arch Reinsurance: Data in millions (original)
  - All other companies: Converted from thousands to millions
- **Year**: 2024 fiscal year (most recent full-year data)

## Technical Details

### Files Included

1. **dashboard.html** - Main dashboard interface (26KB)
   - Uses Chart.js library for visualizations
   - Bootstrap-inspired responsive design
   - Vanilla JavaScript for interactivity

2. **dashboard_data.json** - Financial data in JSON format
   - Contains 10 companies' financial statements
   - Includes calculated ratios
   - All values in USD Millions

3. **run_dashboard.py** - Python server script
   - Simple HTTP server
   - Auto-opens browser
   - Press Ctrl+C to stop

### Browser Compatibility

- Chrome/Edge: ✓ Fully supported
- Firefox: ✓ Fully supported
- Safari: ✓ Fully supported
- IE11: ✗ Not supported (uses modern JavaScript)

## Tips for Analysis

1. **Peer Comparison**: Use the comparison table to identify industry leaders
2. **Profitability Analysis**: Compare ROE and ROA across companies
3. **Risk Assessment**: Look at Equity Ratio and Loss Reserves
4. **Growth Indicators**: Compare revenue growth between companies
5. **Efficiency Metrics**: Loss Ratio and Combined Ratio show underwriting health

## Troubleshooting

### Port 8000 Already in Use
If port 8000 is already in use, try:
```bash
python -m http.server 8001
```
Then open: `http://localhost:8001/dashboard.html`

### Charts Not Loading
- Make sure `dashboard_data.json` is in the same directory as `dashboard.html`
- Check browser console (F12) for errors
- Refresh the page (Ctrl+R)

### No Companies Showing
- Click "Select All" button to populate all companies
- Check that all company checkboxes are visible

## Future Enhancements

Potential improvements for v2.0:

1. **Historical Data**: Add 2023, 2022 data for trend analysis
2. **Export Options**: Export charts as PNG/PDF, export table as CSV/Excel
3. **Custom Ratios**: Ability to create and calculate custom metrics
4. **Comparative Analysis**: Show year-over-year changes
5. **Risk Metrics**: Add additional risk ratios (leverage, liquidity)
6. **Search/Filter**: Search for specific companies
7. **Mobile View**: Optimized mobile dashboard
8. **Data Upload**: Update with new financial data via file upload
9. **Benchmark Lines**: Industry average lines on charts
10. **Annotations**: Add notes and insights to charts

## Questions or Issues?

For questions about:
- **Data accuracy**: See UNITS_CONVERSION_SUMMARY.md
- **Financial definitions**: Consult standard insurance glossary
- **Dashboard bugs**: Check browser console (F12) for JavaScript errors

---

**Dashboard Version**: 1.0
**Data Year**: 2024
**Currency**: USD Millions
**Last Updated**: March 7, 2026

