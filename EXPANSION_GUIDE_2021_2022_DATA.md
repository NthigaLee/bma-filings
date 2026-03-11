# BMA Filings Dashboard - Expansion Guide: Adding 2021-2022 Historical Data
## Preparation & Implementation Strategy

**Document Version:** 1.0
**Date:** March 10, 2026
**Status:** Ready for Implementation (Validation Required)
**Estimated Effort:** 8-10 hours

---

## Overview

This guide provides step-by-step instructions for adding 2021-2022 historical data to the BMA Filings Dashboard. The flexible infrastructure created in Phase 2 supports this expansion, but data quality validation is required before production deployment.

**Current State:**
- ✅ Flexible extraction script ready (`extract_multi_year_dashboard_data.py`)
- ✅ Source files available (`BMA_Class4_2021.xlsx`, `BMA_Class4_2022.xlsx`)
- ✅ Dashboard UI prepared (year selector includes 2021-2022 options)
- ❌ Data quality validation not yet completed
- ❌ Unit conversions not yet verified

**Success Criteria:**
- Data quality score ≥ 95/100 for both years
- No critical errors in balance sheet equations
- All 9 financial ratios calculated correctly
- Documentation of any deviations or adjustments

---

## Pre-Implementation Checklist

### Phase 1: Environment Setup (30 minutes)

- [ ] Verify source files exist and are readable
  ```bash
  ls -lh data/by_year/BMA_Class4_*.xlsx
  ```

- [ ] Verify Python environment has required packages
  ```bash
  python -c "import openpyxl, json; print('OK')"
  ```

- [ ] Create backup of current dashboard_data.json
  ```bash
  cp dashboard_data.json dashboard_data_2024_backup.json
  ```

- [ ] Create git branch for experimental work
  ```bash
  git checkout -b feature/add-2021-2022-data
  ```

### Phase 2: Data Inspection (1 hour)

- [ ] Examine BMA_Class4_2021.xlsx structure
  - Open in Excel/Python
  - Check sheet names (expected: "Balance Sheet", "Income Statement", etc.)
  - Verify company names and columns
  - Check data units (thousands or millions?)
  - Look for any data quality issues

- [ ] Examine BMA_Class4_2022.xlsx structure
  - Same checks as 2021
  - Compare format with 2021
  - Note any structural differences

- [ ] Create inspection report
  ```
  2021 Data Inspection:
  - Sheets: Balance Sheet, Income Statement, Cash Flows
  - Company names: [list differences from current]
  - Data units: [thousands/millions?]
  - Data quality: [observations]

  2022 Data Inspection:
  - [same format]
  ```

### Phase 3: Configuration (30 minutes)

- [ ] Update EXTRACTION_CONFIG in `extract_multi_year_dashboard_data.py`
  ```python
  EXTRACTION_CONFIG = {
      'years': [2021, 2022, 2023, 2024],  # Add 2021-2022
      'workbook_sources': {
          2021: 'data/by_year/BMA_Class4_2021.xlsx',
          2022: 'data/by_year/BMA_Class4_2022.xlsx',
          2023: 'data/BMA_Statements_40_Companies_2023_MILLIONS.xlsx',
          2024: 'data/BMA_Statements_40_Companies_2024_MILLIONS.xlsx',
      },
      'target_companies': [40 company list]  # Use current list
  }
  ```

- [ ] Create test configuration
  ```python
  TEST_CONFIG = {
      'years': [2021],  # Extract just 2021 first
      'workbook_sources': {...},
      'target_companies': [40]
  }
  ```

---

## Extraction & Validation Process

### Step 1: Extract 2021 Data Only (30 minutes)

**Purpose:** Validate extraction on single year before attempting full range

**Instructions:**

1. **Create test extraction script:**
   ```bash
   cp extract_multi_year_dashboard_data.py extract_test_2021.py
   # Edit to use TEST_CONFIG with 2021 only
   ```

2. **Run extraction:**
   ```bash
   python extract_test_2021.py
   ```

3. **Check output:**
   - Verify no errors in console
   - Check dashboard_data.json file size (should be ~20-25 KB for 1 year)
   - Verify company count (should be ≤40, likely 25-30 for 2021)

4. **Review extraction report:**
   - Look for companies with $0M in all metrics (likely missing)
   - Look for unit inconsistencies
   - Note which companies were successfully extracted

5. **Document findings:**
   ```
   2021 Extraction Results:
   - Companies found: [X out of 40]
   - Missing: [list companies with no data]
   - Potential unit issues: [list any]
   - Data quality observations: [notes]
   ```

### Step 2: Validate 2021 Data (1 hour)

**Purpose:** Run comprehensive validation to identify issues

**Instructions:**

1. **Run validation on 2021 data:**
   ```bash
   python validate_financial_data.py
   # (Modify to use single-year config)
   ```

2. **Review validation report:**
   - Check completeness score
   - Review any errors (expected: missing company data)
   - Review warnings (investment composition gaps expected)
   - Identify unusual items

3. **Analyze results:**
   ```
   Expected Issues:
   - Some companies missing (not in Class4 2021)
   - Investment composition incomplete

   Unexpected Issues:
   - Unit mismatches? (thousands vs millions)
   - Calculation errors?
   - Data format issues?
   ```

4. **Unit Conversion Check:**

   If values appear to be in thousands:
   ```python
   # Values appear 100x too small?
   # May need conversion:
   def convert_thousands_to_millions(value):
       return value / 1000

   # Example: If Arch Reinsurance shows $700M assets in 2024
   # but 2021 shows $70M, likely in thousands
   ```

### Step 3: Spot Check Against Source (1-2 hours)

**Purpose:** Verify extraction accuracy

**Instructions:**

1. **Select 3-5 companies from 2021 data**
   - Choose mix of sizes (large, medium, small)
   - Prefer companies that exist in both 2024 and 2021

2. **Find original PDF statements:**
   - Look in `data/pdfs/` or similar
   - Expected filename format: `[Company Name]_2021_financial_statements.pdf`
   - If not found, may need to obtain from company websites

3. **Manually check metrics:**
   - Total Assets: Extract from balance sheet
   - Total Equity: Extract from balance sheet
   - Net Income: Extract from income statement
   - Loss Ratio: Losses & LAE / Net Premiums Earned

4. **Compare results:**
   ```
   Company: Arch Reinsurance (2021)

   Metric               Dashboard   PDF     Variance  Status
   Total Assets         $52,100M    $52,095M  +5M    ✓ OK
   Total Equity         $12,400M    $12,400M  $0M    ✓ OK
   Net Income           $450M       $450M     $0M    ✓ OK
   Loss Ratio %         38.2%       38.2%     0.0%   ✓ OK
   ```

5. **Document accuracy:**
   - Calculate average variance
   - Note any systematic bias
   - Flag companies with issues

### Step 4: Extract 2022 Data (30 minutes)

**Purpose:** Extract second historical year

**Instructions:**

1. **Update configuration for 2022:**
   ```python
   TEST_CONFIG = {
       'years': [2022],
       'workbook_sources': {...},
       'target_companies': [40]
   }
   ```

2. **Run extraction:**
   ```bash
   python extract_test_2022.py
   ```

3. **Compare with 2021:**
   - More companies should appear in 2022
   - Structure should match 2021
   - Data quality should be similar or better

### Step 5: Validate All Four Years (1.5 hours)

**Purpose:** Comprehensive validation across full range

**Instructions:**

1. **Update configuration for full range:**
   ```python
   EXTRACTION_CONFIG = {
       'years': [2021, 2022, 2023, 2024],
       'workbook_sources': {...},
       'target_companies': [40]
   }
   ```

2. **Run full extraction:**
   ```bash
   python extract_multi_year_dashboard_data.py
   ```

3. **Run validation:**
   ```bash
   python validate_financial_data.py
   ```

4. **Review results:**
   - Overall quality score (target: ≥95/100)
   - Year-over-year consistency (transitions between formats)
   - Data gap analysis (expected: fewer companies in 2021)
   - Error categorization

5. **Make go/no-go decision:**
   ```
   Quality Score Assessment:
   - 2021: [score] - [decision: proceed/investigate]
   - 2022: [score] - [decision: proceed/investigate]
   - 2023: [score] - [decision: proceed/investigate]
   - 2024: [score] - [decision: proceed/investigate]

   Overall: [PROCEED/HALT] if score ≥ 95/100
   ```

---

## Handling Data Issues

### Issue 1: Unit Mismatches (Thousands vs. Millions)

**Symptom:** 2021 assets are 100x smaller than 2024 for same company

**Diagnosis:**
```python
# Check if values need conversion
arch_2024 = 70702  # millions
arch_2021 = 527    # might be thousands

# If values are in thousands:
if arch_2021 < arch_2024 * 0.1:
    arch_2021_corrected = arch_2021 * 1000  # 527,000M
```

**Solution Options:**

Option A: Detect and convert automatically
```python
def normalize_units(data, year):
    """Detect and fix unit mismatches"""
    if year < 2023:  # Historical data
        # Check if values seem too small
        avg_assets = calculate_average(data, 'Total Assets')
        if avg_assets < 1000:  # Average < $1B seems wrong
            # Convert all values
            for company in data:
                for metric in data[company]:
                    data[company][metric] *= 1000
    return data
```

Option B: Manual conversion with documentation
```python
# Document conversion in comments
# 2021-2022 values from BMA_Class4 format (in thousands)
# Converted to millions for consistency
CONVERSION_FACTOR_2021_2022 = 1000
```

Option C: Use separate configuration
```python
EXTRACTION_CONFIG = {
    'years': [2021, 2022, 2023, 2024],
    'unit_conversions': {
        2021: 1000,  # Convert thousands to millions
        2022: 1000,
        2023: 1,     # Already in millions
        2024: 1,
    }
}
```

**Recommendation:** Use Option A (automatic detection) with documentation

### Issue 2: Missing Companies in Historical Years

**Symptom:** Only 25 companies found in 2021 vs 40 in 2024

**Root Cause:** Not all companies existed or filed in 2021

**Analysis:**
```
2021 Company Coverage:
✓ Present: Arch, Ascot, Aspen, AXIS, etc. (25 companies)
✗ Missing: ABR Reinsurance, Allied World, Convex, etc. (15 companies)

Why Missing:
- Companies founded after 2021
- Not part of BMA Class 4 in 2021
- Not required to file in 2021
- Business entered Bermuda later
```

**Solution:**
1. Document which companies missing
2. Note expected coverage by year:
   - 2021: 25-28 companies (70%)
   - 2022: 32-35 companies (80%)
   - 2023: 35-38 companies (87%)
   - 2024: 40 companies (100%)

3. Add footnote to dashboard:
   ```
   "Note: 2021-2022 data includes 25-35 companies based on
   availability. Not all current 40 companies filed in earlier years."
   ```

### Issue 3: Company Name Mismatches

**Symptom:** Company name in 2021 workbook differs from current name

**Examples:**
- "XL Bermuda Ltd." vs. "XL Bermuda"
- "Ace Bermuda" (old name for AXIS, maybe)
- "AIG Bermuda" vs. "American International Reinsurance"

**Solution:** Update company discovery fuzzy matching
```python
# Add name mapping dictionary
COMPANY_NAME_MAPPING = {
    "XL Bermuda Ltd.": "XL Bermuda",
    "Ace Bermuda": "AXIS Specialty",
    # Add more mappings as discovered
}

# Use in discovery:
if company_name in COMPANY_NAME_MAPPING:
    company_name = COMPANY_NAME_MAPPING[company_name]
```

### Issue 4: Balance Sheet Doesn't Balance

**Symptom:** Assets ≠ Liabilities + Equity in some 2021 companies

**Diagnosis:**
```
Expected: Assets = Liabilities + Equity
Example: 10,000 ≠ 8,000 + 1,500 (difference of 500)

Possible causes:
- Unit mismatch (parts in thousands, parts in millions)
- Rounding or truncation in source data
- Data entry errors in original workbook
- Different accounting periods
```

**Solution:**
1. Accept tolerance of ±1% (same as validation)
2. Document any larger discrepancies
3. Flag for manual review
4. Adjust validation threshold if necessary

---

## Dashboard Updates for Historical Data

### Update 1: Dashboard Configuration

**File:** `dashboard.html` (already prepared)

**Status:** ✅ Year selector already includes 2021-2022 options
```html
<select id="year-filter">
    <option value="2024">2024</option>
    <option value="2023">2023</option>
    <option value="2022">2022</option>  <!-- Ready -->
    <option value="2021">2021</option>  <!-- Ready -->
</select>
```

**No changes needed** - UI already supports 4-year data

### Update 2: Add Historical Data Disclaimer

**File:** Create `HISTORICAL_DATA_DISCLAIMER.md`

```markdown
## Historical Data (2021-2022)

### Data Coverage by Year

**2021:** 25-28 companies (~70% of current 40)
**2022:** 32-35 companies (~87% of current 40)
**2023:** 35-40 companies (~87% of current 40)
**2024:** 40 companies (100%)

### Quality Notes

- 2021-2022 data extracted from legacy BMA Class 4 workbooks
- Company coverage incomplete in early years (not all companies filed)
- Investment composition not available for 2021-2022
- Investment gains/losses unavailable (all companies, all years)
- Accounting standards may vary by company

### Recommendations

- Use 2023-2024 for current analysis (most complete, highest quality)
- Use 2021-2022 for trend analysis (longer history) with caveats
- Compare within same-year peer groups only
- Document year span when citing metrics
```

### Update 3: Add Data Quality Indicators

**File:** `dashboard.html` (in data loading section)

```javascript
// Add data quality metadata
const dataQualityMetadata = {
    2024: { companies: 40, quality: 99, completeness: 100 },
    2023: { companies: 35, quality: 99, completeness: 87 },
    2022: { companies: 32, quality: 95, completeness: 80 },  // Example
    2021: { companies: 25, quality: 93, completeness: 62 }   // Example
};

// Display quality badge based on year
function getDataQualityBadge(year) {
    const meta = dataQualityMetadata[year];
    if (!meta) return "Unknown";
    if (meta.quality >= 99) return "Excellent ✓";
    if (meta.quality >= 95) return "Good ⚠";
    if (meta.quality >= 90) return "Fair ⚠⚠";
    return "Limited";
}
```

---

## Testing & Verification

### Test Suite 1: Data Extraction

```bash
# Test 1: Extract 2021 only
python -c "
from extract_multi_year_dashboard_data import MultiYearExtractor, EXTRACTION_CONFIG
config = EXTRACTION_CONFIG.copy()
config['years'] = [2021]
extractor = MultiYearExtractor(config)
data = extractor.extract_all()
print(f'Companies in 2021: {len(data[\"companies\"])}')
"

# Test 2: Extract 2022 only
# ... (repeat with years: [2022])

# Test 3: Extract full range
python extract_multi_year_dashboard_data.py
```

### Test Suite 2: Data Validation

```bash
# Run validation
python validate_financial_data.py

# Expected output:
# Data Quality Score: 94-98/100 (slightly lower than 99 due to gaps)
# Errors: <20 (mostly missing company data)
# Warnings: 40-50 (investment composition gaps)
# YoY Changes: 5-10 (normal for historical expansion)
```

### Test Suite 3: Dashboard Rendering

```bash
# 1. Update dashboard_data.json with 4 years
# 2. Reload dashboard in browser
# 3. Test each year in dropdown:
#    - 2024: Should show all 40 companies
#    - 2023: Should show 35 companies
#    - 2022: Should show ~32 companies
#    - 2021: Should show ~25 companies
# 4. Verify charts render for each year
# 5. Check metrics update with year selection
```

### Test Suite 4: Spot Checks

```python
# Spot check 5 companies across years
spot_check_companies = [
    "Arch Reinsurance",
    "Renaissance Reinsurance",
    "XL Bermuda",
    "Validus Reinsurance",
    "Partner Reinsurance Company"
]

for company in spot_check_companies:
    for year in [2021, 2022, 2023, 2024]:
        # Verify data exists
        # Check reasonableness of values
        # Verify calculations
        print(f"{company} {year}: OK")
```

---

## Deployment Process

### Step 1: Final Validation (30 minutes)

```bash
# 1. Run full validation
python validate_financial_data.py > validation_final.txt

# 2. Review results
cat validation_final.txt

# 3. Confirm quality score ≥ 95/100
# 4. Document any exceptions
```

### Step 2: Create Historical Data Files

```bash
# Create Excel workbooks for archival
# BMA_Statements_40_Companies_2021_MILLIONS.xlsx
# BMA_Statements_40_Companies_2022_MILLIONS.xlsx

# These can be generated from extracted data:
python -c "
import json
from openpyxl import Workbook

# Load extracted data
with open('dashboard_data.json') as f:
    data = json.load(f)

# Generate Excel files for 2021-2022
for year in [2021, 2022]:
    # Create workbook...
    # Save as BMA_Statements_40_Companies_{year}_MILLIONS.xlsx
"
```

### Step 3: Commit & Deploy

```bash
# 1. Update dashboard_data.json with 4 years
cp dashboard_data_4_years.json dashboard_data.json

# 2. Update dashboard_data.js
python -c "
import json
with open('dashboard_data.json') as f:
    data = json.load(f)
with open('dashboard_data.js', 'w') as f:
    f.write('const dashboardData = ' + json.dumps(data, indent=2))
"

# 3. Create documentation files
cp HISTORICAL_DATA_DISCLAIMER.md docs/

# 4. Commit
git add dashboard_data.json dashboard_data.js HISTORICAL_DATA_DISCLAIMER.md
git commit -m "Add 2021-2022 historical data for 25-35 companies

- Extract 2021-2022 data using flexible pipeline
- Validate across 4-year range (quality: 95/100+)
- Add year selector to dashboard
- Document coverage gaps and limitations
- Maintain 99/100 quality for 2023-2024
"

# 5. Push
git push origin feature/add-2021-2022-data

# 6. Create pull request
gh pr create --title "Add 2021-2022 historical data" \
  --body "Expands dashboard from 2 years to 4 years..."
```

### Step 4: Review & Merge

- [ ] Code review of extraction script
- [ ] Validation of data quality
- [ ] Testing on staging environment
- [ ] Approval from project lead
- [ ] Merge to main branch

### Step 5: Deploy to Production

```bash
# Switch to main and update
git checkout main
git pull origin main

# Verify deployment
curl https://nthigalee.github.io/bma-filings/dashboard.html | grep "year-filter"
# Should show year selector with 2021 option
```

---

## Rollback Plan

If issues are discovered after deployment:

```bash
# 1. Quick rollback
git revert [commit-hash]
git push origin main

# 2. Restore from backup
cp dashboard_data_2024_backup.json dashboard_data.json
git add dashboard_data.json
git commit -m "Rollback to 2024 data only"
git push origin main

# 3. Investigate issue
# Fix root cause
# Re-test locally
# Redeploy when ready
```

---

## Expected Results

After successful implementation:

✅ **Dashboard Features:**
- Year selector shows 2021-2024 options
- Charts display for each year
- Metrics update when year changes
- Company filter works for each year

✅ **Data Quality:**
- 2024: 99/100 quality, 40 companies
- 2023: 99/100 quality, 35 companies
- 2022: 95+/100 quality, 32 companies
- 2021: 95+/100 quality, 25 companies

✅ **Documentation:**
- Data gaps clearly documented
- Quality metadata available
- Historical disclaimers visible
- Recommendations provided

✅ **File Sizes:**
- dashboard_data.json: ~150-200 KB (4x larger)
- dashboard_data.js: ~150-200 KB
- Validation report: ~75 KB

---

## Timeline Estimate

| Phase | Task | Duration | Total |
|-------|------|----------|-------|
| 1 | Setup & inspection | 1.5 hours | 1.5h |
| 2 | Extract 2021 only | 0.5 hours | 2h |
| 3 | Validate 2021 | 1 hour | 3h |
| 4 | Spot checks | 1.5 hours | 4.5h |
| 5 | Extract 2022 | 0.5 hours | 5h |
| 6 | Validate all 4 years | 1.5 hours | 6.5h |
| 7 | Dashboard updates | 1 hour | 7.5h |
| 8 | Testing & refinement | 1.5 hours | 9h |
| 9 | Commit & deploy | 1 hour | 10h |

**Total Estimated Effort: 8-10 hours**

---

## Success Criteria Checklist

- [ ] Data quality score ≥ 95/100 for all years
- [ ] No critical errors in balance sheet equations
- [ ] All 9 financial ratios calculated correctly
- [ ] Spot checks pass for 5+ companies
- [ ] Dashboard displays all 4 years without errors
- [ ] Year selector functional for 2021-2024
- [ ] Charts render correctly for each year
- [ ] Company filter works for each year
- [ ] Documentation complete and accurate
- [ ] Validation report reviewed and approved

---

## Post-Implementation Actions

### Immediate (Day 1)
- [ ] Monitor dashboard for user feedback
- [ ] Check browser console for errors
- [ ] Verify data loads quickly (<3 seconds)

### Week 1
- [ ] Gather user feedback on historical data
- [ ] Fix any reported issues
- [ ] Update documentation if needed

### Month 1
- [ ] Analyze usage patterns for 2021-2022 data
- [ ] Gather requirements for further enhancements
- [ ] Plan next phase improvements

---

## References

- Phase 2 Technical Documentation: `PHASE_2_TECHNICAL_DOCUMENTATION.md`
- Data Quality Report: `DATA_QUALITY_AND_GAPS_REPORT.md`
- Flexible Extraction Script: `extract_multi_year_dashboard_data.py`
- Validation Suite: `validate_financial_data.py`

---

**Document Prepared By:** Claude Haiku 4.5
**Last Updated:** March 10, 2026
**Status:** Ready for Implementation
