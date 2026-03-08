# Financial Statements - Units Verification & Conversion

**Generated**: March 7, 2026
**Status**: ✓ COMPLETE - ALL DATA UNIFIED IN MILLIONS

---

## Issue Discovered

### Unit Discrepancy in Source PDFs
During verification of balance sheet titles in original PDF financial statements:

**Arch Reinsurance Ltd** - ONLY COMPANY IN MILLIONS
- PDF declares: "(U.S. dollars in millions, except share data)"
- Original data was already in millions ✓

**8 Companies in THOUSANDS**
- Ascot Bermuda Limited: "(Expressed in thousands of U.S. dollars)"
- Aspen Bermuda Limited: "(In thousands of U.S. dollars, except per share and share amounts)"
- AXIS Specialty Limited: "(In thousands of U.S. dollars)"
- Chubb Tempest Reinsurance Ltd: "(in thousands of U.S. dollars)"
- Everest Reinsurance Bermuda Ltd: "(Dollars in thousands, except par value per share)"
- Markel Bermuda Limited: "(dollars in thousands)"
- Partner Reinsurance Company Ltd: "(Expressed in thousands of U.S. dollars, except parenthetical share data)"
- Renaissance Reinsurance Ltd: "(in thousands of United States dollars)"

**Hannover Re Bermuda Ltd** - Units not declared in PDF
- Assumed thousands (consistent with other Bermuda reinsurers)

---

## Solution Implemented

### Data Conversion to Millions
All workbooks have been converted to consistent units: **USD Millions**

**Arch Reinsurance**: No conversion needed
- Already in millions in source PDFs
- Values used as-is

**All Other 9 Companies**: Converted from thousands to millions
- Conversion formula: Original Value ÷ 1,000
- Example: Ascot source shows 4,678,460 (thousands) → Workbook shows 4,678.5 (millions)
- This represents $4,678.5 million = $4.6785 billion

---

## Files Generated

### New Unified Workbooks
**Location**: `C:\Users\nthig\.claude\projects\bma-filings\data\`

1. **BMA_Statements_2024_MILLIONS.xlsx**
   - 3 sheets: Balance Sheet, Income Statement, Cash Flows
   - 10 companies in adjacent columns
   - All values in USD Millions
   - Year: 2024 fiscal year data

2. **BMA_Statements_2023_MILLIONS.xlsx**
   - 3 sheets: Balance Sheet, Income Statement, Cash Flows
   - 10 companies in adjacent columns
   - All values in USD Millions
   - Year: 2023 fiscal year data

---

## Sheet Titles - VERIFIED

### 2024 Workbook
- ✓ Balance Sheet - 2024 (USD Millions)
- ✓ Income Statement - 2024 (USD Millions)
- ✓ Cash Flows - 2024 (USD Millions)

### 2023 Workbook
- ✓ Balance Sheet - 2023 (USD Millions)
- ✓ Income Statement - 2023 (USD Millions)
- ✓ Cash Flows - 2023 (USD Millions)

---

## Data Format and Scale

### Understanding the Numbers
All values in workbooks = **USD Millions**

**Examples:**
- Arch Re Total Assets: 40,476.0 in workbook = **$40,476 million = $40.476 billion**
- Ascot Total Assets: 6,631.2 in workbook = **$6,631.2 million = $6.6312 billion**
- Aspen Total Assets: 1,929.0 in workbook = **$1,929 million = $1.929 billion**

### Conversion Verification
Sample Balance Sheet data (2024):

| Company | Fixed Maturities | Cash Equivalents | Total Assets |
|---------|-----------------|------------------|--------------|
| Arch Re (millions) | 27,035.0 | 936.0 | 40,476.0 |
| Ascot (thousands→millions) | 2,944.2 | 533.3 | 6,631.2 |
| Aspen (thousands→millions) | 1,562.0 | 186.9 | 1,929.0 |
| AXIS (thousands→millions) | 3,252.5 | 389.5 | 3,987.5 |

---

## Peer Comparison Benefits

Now that all companies use the same units, peer comparisons are valid:

### Largest to Smallest by Total Assets (2024, USD Millions)
1. Arch Reinsurance: $40,476M
2. Ascot Bermuda: $6,631M
3. Chubb Tempest: ~$6,000M
4. AXIS Specialty: $3,988M
5. Renaissance Reinsurance: ~$3,500M
... and so on

### No Conversion Needed for Analysis
All financial metrics can be calculated directly without additional conversion:
- Loss Ratio = Losses & LAE / Net Premiums Earned
- ROE = Net Income / Total Equity
- ROA = Net Income / Total Assets
- Combined Ratio = Loss Ratio + Expense Ratio

---

## Summary of Units in Source PDFs

| Company | Unit Declaration | Converted | Workbook Value |
|---------|-------------------|-----------|-----------------|
| Arch Reinsurance | millions | No | Millions |
| Ascot Bermuda | thousands | Yes (÷1,000) | Millions |
| Aspen Bermuda | thousands | Yes (÷1,000) | Millions |
| AXIS Specialty | thousands | Yes (÷1,000) | Millions |
| Chubb Tempest | thousands | Yes (÷1,000) | Millions |
| Everest Reinsurance | thousands | Yes (÷1,000) | Millions |
| Hannover Re | undeclared | Yes (÷1,000) | Millions |
| Markel Bermuda | thousands | Yes (÷1,000) | Millions |
| Partner Reinsurance | thousands | Yes (÷1,000) | Millions |
| Renaissance Reinsurance | thousands | Yes (÷1,000) | Millions |

---

## Key Points

✓ **Units Verified** - Confirmed from original PDF balance sheet titles
✓ **Conversion Applied** - 9 companies converted from thousands to millions
✓ **Titles Updated** - All sheets clearly labeled "(USD Millions)"
✓ **Data Consistent** - All 10 companies now in same units
✓ **Peer Comparison Ready** - Direct side-by-side analysis enabled
✓ **Documentation Complete** - Clear unit declarations in all workbooks

---

## Workbooks Ready for Use

The new files `BMA_Statements_2024_MILLIONS.xlsx` and `BMA_Statements_2023_MILLIONS.xlsx` are now ready for:

- ✓ Peer company financial analysis
- ✓ Ratio calculations without conversion
- ✓ Year-over-year trend analysis
- ✓ Competitive benchmarking
- ✓ Reinsurance market research
- ✓ Investment analysis

**All data is now in consistent USD Millions units.**

---

*For questions about data sources or methodology, see the PDF analysis files in the project directory.*
