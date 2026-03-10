# Investment Metrics Guide
## BMA Filings Financial Dashboard

**Date:** March 10, 2026
**Version:** 1.0
**Applies to:** 40 Bermuda Insurance/Reinsurance Companies (2023-2024)

---

## Overview

The BMA Filings Dashboard includes three key investment metrics that help analyze how effectively Bermuda insurance companies manage their investment portfolios. These metrics are derived from:

- **Balance Sheet Data:** Total Investments
- **Income Statement Data:** Net Investment Income and Investment Gains/Losses
- **Calculated Ratios:** Derived from the above items

---

## Investment Metrics Explained

### 1. Investment Return (%)

**Formula:**
```
Investment Return % = (Net Investment Income + Investment Gains/Losses) / Total Investments * 100
```

**Definition:**
The annual percentage return on all invested capital, including both actual income (interest, dividends) and realized/unrealized gains or losses on investments.

**Interpretation:**
- **Typical Range:** 2% to 8% for conservative insurance portfolios
- **Better Performance:** Higher returns indicate more effective capital management
- **Caution:** Very high returns (>10%) may indicate excessive risk-taking
- **Low Returns:** <2% may indicate overly conservative positioning

**Example:**
- Company A: Total Investments = $5,000M, Net Investment Income = $150M, Gains = $50M
- Calculation: ($150M + $50M) / $5,000M × 100 = **4.0%**

---

### 2. Investment Yield (%)

**Formula:**
```
Investment Yield % = Net Investment Income / Total Investments * 100
```

**Definition:**
The percentage of annual income generated from investments, excluding gains/losses. More conservative than Investment Return.

**Interpretation:**
- **Typical Range:** 2% to 4% for most insurance portfolios
- **Reflects Market Conditions:** Rising/falling with interest rates
- **Quality:** More stable, predictable measure than total return

**Example:**
- Company A: Total Investments = $5,000M, Net Investment Income = $150M
- Calculation: $150M / $5,000M × 100 = **3.0%**

---

### 3. Investments to Assets (%)

**Formula:**
```
Investments to Assets % = Total Investments / Total Assets * 100
```

**Definition:**
Shows what percentage of total assets are deployed as investments versus other assets (cash, receivables, etc.).

**Interpretation:**
- **Typical Range:** 40% to 70% for insurance companies
- **Higher (60-70%):** Relies on investment income, more market exposure
- **Lower (40-50%):** More conservative, higher liquidity reserves

**Example:**
- Company A: Total Assets = $10,000M, Total Investments = $6,500M
- Calculation: $6,500M / $10,000M × 100 = **65%**

---

## Typical Ranges by Company Size

### Large Global Reinsurers (>$10B assets)
- Investment Return: 3.5% - 5.5%
- Investment Yield: 2.5% - 4.0%
- Investments to Assets: 55% - 70%

### Mid-Size Reinsurers ($2-10B assets)
- Investment Return: 3.0% - 5.0%
- Investment Yield: 2.0% - 3.5%
- Investments to Assets: 50% - 65%

### Specialty Insurers (<$2B assets)
- Investment Return: 2.5% - 4.5%
- Investment Yield: 1.5% - 3.0%
- Investments to Assets: 45% - 60%

---

## Data Quality Status

### Investment Income
- **Status:** 100% complete (all 40 companies)
- **Actual Data:** ~33% (from PDFs)
- **Estimated Data:** ~67% (using industry-standard yields)
- **Confidence:** Good for reported, Fair for estimated

### Investment Gains/Losses
- **Status:** All values currently $0M (placeholder)
- **Issue:** Not extracted from financial statements
- **Recommendation:** Extract from 10-K filings for accuracy

### Investment Composition
- **Status:** Not yet broken down by type
- **Needed:** Fixed Maturities, Equities, Short-term, Other
- **Recommendation:** Extract detailed breakdown

---

## Known Limitations

1. **2023 Data Gaps:** 5 of 10 additional companies have incomplete 2023 balance sheet data
2. **Investment Gains/Losses:** Currently $0M (all values); actual gains/losses not captured
3. **Investment Composition:** Not broken down by asset type or duration
4. **Accounting Variations:** Companies may use different standards (IFRS vs US GAAP)

---

## Future Enhancements

### High Priority
- [ ] Extract investment gains/losses from 10-K filings
- [ ] Populate missing 2023 data for 5 companies
- [ ] Calculate investment composition percentages

### Medium Priority
- [ ] Add 2021-2022 historical data
- [ ] Create peer group benchmarks
- [ ] Add quarterly data

### Lower Priority
- [ ] Investment composition visualization charts
- [ ] Risk metrics (duration, credit quality)
- [ ] ESG/sustainable investing metrics

---

**Document Version:** 1.0
**Last Updated:** March 10, 2026
**Dashboard URL:** https://nthigalee.github.io/bma-filings/dashboard.html

