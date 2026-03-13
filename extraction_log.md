# BMA Filings Data Extraction Log

**Date:** 2026-03-12
**Script:** `fill_gaps.py`
**New values merged:** 98 (into `dashboard_data.json` / `dashboard_data.js`)

---

## Extraction Method

- **Tool:** PyMuPDF (fitz) for fast text extraction from PDFs
- **Denomination detection:** Searches for "in thousands" / "in millions" in the PDF text; defaults to thousands for BMA Class 4 filings
- **Unit conversion:** If "thousands" → divide by 1,000; if "millions" → keep as-is
- **False-positive prevention:** Line-anchored regex patterns (`^metric_label`) to avoid matching metric names that appear in non-table contexts (e.g. "recognized in net income")
- **Year exclusion:** Numbers in range 2015–2029 rejected as financial values
- **Merge policy:** Only fills gaps (existing non-zero values preserved) unless prior value is clearly implausible (too small for the metric type)

---

## Results by Company

| Company | 2023 PDF | 2024 PDF | Fields Extracted | New Merged | Notes |
|---------|----------|----------|-----------------|------------|-------|
| **Brit Reinsurance Bermuda Limited** | NO PDF | IMAGE | 0 | 0 | 2024 PDF is image-only; no 2023 PDF in collection |
| **Fortitude International Reinsurance Ltd.** | ✓ | ✓ | 7+8 | 15 | TA, TI, TL, Cash, NI extracted; no NPE |
| **Antares Reinsurance Company Limited** | ✓ | ✓ | 1+4 | 2 | Only TE found; TA for 2024 was pre-existing |
| **Everest International Reinsurance Ltd.** | ✓ | ✓ | 9+9 | 12 | Full balance sheet; NPE extracted; **loss/combined ratios flagged >150%/200% → zeroed** |
| **Hannover Re Bermuda** | ✓ | ✓ (partial) | 7+4 | 4 | 2023: complete. 2024 balance sheet is image-only; TE from equity statement (manual patch = 2583.9M); IFRS 17 format (GPW from "Reinsurance revenue (gross)") |
| **ABR Reinsurance Ltd.** | ✓ | ✓ | 9+9 | 11 | Full data. **Total Expenses negative in PDF (deduction format) → excluded. Loss Ratio >150% → zeroed** |
| **Allied World Assurance Company Ltd** | ✓ | ✓ | 9+8 | 17 | Near-complete; "expressed in millions"; Fixed stale TA=22.2M→22163.7M and TE=6.7M→5162.1M (prior extractions were wrong units) |
| **Convex Re Limited** | ✓ | ✓ | 13+13 | 14 | Full data; "expressed in thousands" |
| **DaVinci Reinsurance Ltd.** | ✓ | ✓ | 10+10 | 10 | Full data; NPE fixed (5.0M→987.4M); **Losses and LAE negative in PDF → excluded; Combined Ratio zeroed** |
| **American International Reinsurance Company Ltd.** | ✓ | ✓ | 5+4 | 4 | Only TA extracted; no TE/NI/NPE found; pre-existing TE=2.0M is bad but no replacement data available |
| **Argo Re Ltd.** | ✓ | ✓ | 5+7 | 5 | TA+TE extracted; no NI/NPE (not matched by patterns) |
| **Markel Bermuda** | ✓ | ✓ | 10+11 | 5 | TA+TE+NI for both years |
| **XL Bermuda** | ✓ | ✓ | 4+4 | 0 | All data pre-existing; extraction confirms TA~65B (pre-existing 34.7B may be different entity/entity scope) |

---

## Outlier Flags (excluded from dashboard ratios)

All flagged ratios are set to 0 in the dashboard (underlying data values retained where they passed bounds):

| Company | Year | Metric | Value | Reason |
|---------|------|--------|-------|--------|
| Everest International Reinsurance Ltd. | 2023 | Loss Ratio | 216.6% | >150% threshold |
| Everest International Reinsurance Ltd. | 2023 | Combined Ratio | 216.6% | >200% threshold |
| Everest International Reinsurance Ltd. | 2024 | Loss Ratio | 238.3% | >150% threshold |
| Everest International Reinsurance Ltd. | 2024 | Combined Ratio | 238.3% | >200% threshold |
| ABR Reinsurance Ltd. | 2023 | Total Expenses | -609.8M | Negative (deduction format in PDF) |
| ABR Reinsurance Ltd. | 2023 | Loss Ratio | 181.1% | >150% threshold |
| ABR Reinsurance Ltd. | 2024 | Total Expenses | -600.7M | Negative (deduction format in PDF) |
| ABR Reinsurance Ltd. | 2024 | Loss Ratio | 199.4% | >150% threshold |
| DaVinci Reinsurance Ltd. | 2023 | Losses and LAE | -193.5M | Negative (net presentation in PDF) |
| DaVinci Reinsurance Ltd. | 2023 | Combined Ratio | 47.3% | <50% threshold |
| DaVinci Reinsurance Ltd. | 2024 | Losses and LAE | -151.7M | Negative (net presentation in PDF) |
| DaVinci Reinsurance Ltd. | 2024 | Combined Ratio | 47.2% | <50% threshold |

---

## Remaining Gaps (could not be filled)

- **Brit Reinsurance Bermuda Limited (2023+2024):** No 2023 PDF in collection; 2024 PDF is image-based (requires OCR)
- **Hannover Re Bermuda (2024):** Balance sheet page is image-embedded — Total Assets and Total Investments not available from text extraction. TE=2583.9M sourced manually from Statement of Changes in Shareholders' Equity.
- **American International Reinsurance Co. (both years):** Regex patterns did not match equity/income items in this PDF's layout. Requires manual review.
- **Argo Re Ltd. (both years):** Net Income and Net Premiums Earned not extracted (income statement format not matched).
- **Markel Bermuda (both years):** Net Premiums Earned not extracted (IFRS-style consolidated filing with different label structure).
- **XL Bermuda (2024):** Pre-existing NI=2.0M is likely a prior extraction error (vs extracted 2225.9M), but preserved to avoid overwriting potentially valid data. Recommend manual review.

---

## Technical Notes

- PDFs reporting "expressed in thousands" have all values divided by 1,000 to convert to USD millions
- PDFs reporting "expressed in millions" are used as-is
- ABR and DaVinci use "net" expense presentation where losses appear as negative cash outflows in some tables — the regex correctly excludes these negative values
- Hannover Re 2023/2024 uses IFRS 17 format: "Reinsurance revenue (gross)" mapped to Gross Premiums Written; "Ordinary investment income" mapped to Net Investment Income
- Pre-existing implausible values overwritten: Allied World TA (22.2M→22163.7M), Allied World TE (6.7M→5162.1M), DaVinci NPE (5.0M→987.4M), Allied World GPW (6.7M→6708.5M), Allied World TL (15.7M→16868.9M), Hannover Re TI 2023 (0.4M→4423.8M), Hannover Re TI 2024 (-1.5M→0)
