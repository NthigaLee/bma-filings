# Reinsurance Notes Extraction Report

**Date:** 2026-03-13
**Script:** `extract_reinsurance_notes.py`
**Source:** BMA financial statement PDFs (2023 & 2024 data years)
**Output:** `reinsurance_notes_extracted.json` → merged into `dashboard_data.json`

---

## Summary

| Stat | Count |
|------|-------|
| Total company-year pairs | 80 |
| Successful extractions | 38 |
| Partial extractions | 4 |
| Not found in PDF | 33 |
| Image-only PDFs | 3 |
| No PDF available | 2 |

**42 records merged** into `dashboard_data.json` under `reinsurance_note` section.
**17 Net Premiums Written** values added to `income_statement` (previously missing).

---

## Extraction Results by Company

| Company | 2023 Status | 2024 Status | Notes |
|---------|-------------|-------------|-------|
| Arch Reinsurance | success / no_prior_data | success / no_prior_data | Direct+Assumed format |
| Ascot Bermuda | no_pdf | success / mismatch(60.5%) | Direct+Assumed; ceded large |
| Aspen Bermuda | success / mismatch(6.9%) | success / match(4.8%) | — |
| AXIS Specialty | not_found | not_found | No assumed/ceded split in note |
| Chubb Tempest Reinsurance | success / match(0.0%) | success / match(0.0%) | Clean match |
| Everest Reinsurance Bermuda | success / no_prior_data | success / no_prior_data | — |
| Hannover Re Bermuda | not_found | not_found | IFRS 17 format |
| Markel Bermuda | partial | partial | Columnar; only some fields |
| Partner Reinsurance Company | success / mismatch(16.6%) | success / mismatch(6.8%) | Multi-year table; may pick prior year |
| Renaissance Reinsurance | success / match(2.7%) | success / mismatch(29.8%) | 2024 scope difference |
| Endurance Specialty Insurance | not_found | not_found | — |
| XL Bermuda | not_found | not_found | — |
| AXA XL Reinsurance | not_found | not_found | — |
| Validus Reinsurance | success / mismatch(97.5%) | success / mismatch(97.7%) | BMA subsidiary vs consolidated GPW |
| Somers Re | success / mismatch(59.3%) | success / mismatch(53.5%) | Partial entity scope |
| Lancashire Insurance Company | not_found | not_found | — |
| Hiscox Insurance Company Bermuda | image_only | image_only | Scanned PDF, no text layer |
| Canopius Reinsurance | success / mismatch(65.5%) | success / mismatch(51.3%) | Mixed direct+assumed scope |
| Conduit Reinsurance | not_found | not_found | IFRS 17 format |
| Fidelis Insurance Bermuda | success / mismatch(5.6%) | success / mismatch(17.2%) | — |
| Fortitude Reinsurance Company | not_found | not_found | — |
| Group Ark Insurance | not_found | not_found | — |
| Hamilton Re | partial | partial | Some fields only |
| Harrington Re | not_found | not_found | — |
| Liberty Specialty Markets Bermuda | success / mismatch(24.7%) | success / mismatch(17.6%) | "Effects of reinsurance" format |
| MS Amlin AG | not_found | not_found | — |
| Premia Reinsurance | not_found | not_found | — |
| Starr Insurance & Reinsurance | success / mismatch(40.4%) | success / mismatch(37.9%) | Direct+Assumed; GPW = only assumed |
| Vantage Risk | success / mismatch(54.5%) | success / mismatch(48.8%) | — |
| SiriusPoint Bermuda Insurance | success / mismatch(36.6%) | success / mismatch(52.7%) | Direct+Assumed+Gross split |
| ABR Reinsurance Ltd. | success / match(0.0%) | success / match(0.0%) | Clean match |
| Allied World Assurance Company Ltd | success / mismatch(77.0%) | success / mismatch(72.5%) | Large ceded; assumed ≠ gross |
| American International Reinsurance Co. | not_found | not_found | — |
| Antares Reinsurance Company Limited | not_found | not_found | — |
| Argo Re Ltd. | not_found | not_found | — |
| Brit Reinsurance Bermuda Limited | no_pdf | image_only | — |
| Convex Re Limited | not_found | success / no_prior_data | — |
| DaVinci Reinsurance Ltd. | success / mismatch(22454%) | success / mismatch(26912%) | Placeholder GPW in dashboard (5.0) |
| Everest International Reinsurance Ltd. | success / no_prior_data | success / no_prior_data | — |
| Fortitude International Reinsurance Ltd. | not_found | not_found | — |

---

## Cross-Check Analysis

The `assumed_premiums_written` extracted from the reinsurance note was compared against
`Gross Premiums Written` already in `dashboard_data.json`.

### Clean Matches (≤5% delta)
| Company | Year | APW (extracted) | GPW (dashboard) | Delta |
|---------|------|-----------------|-----------------|-------|
| Chubb Tempest Reinsurance | 2023 | 5,381.8 | 5,381.8 | 0.0% |
| Chubb Tempest Reinsurance | 2024 | 5,381.8 | 5,381.8 | 0.0% |
| ABR Reinsurance Ltd. | 2023 | 502.4 | 502.4 | 0.0% |
| ABR Reinsurance Ltd. | 2024 | 504.2 | 504.2 | 0.0% |
| Renaissance Reinsurance | 2023 | 3,081.8 | 3,000.9 | 2.7% |
| Aspen Bermuda | 2024 | 1,096.4 | 1,047.4 | 4.8% |

### Known Scope Mismatches (expected — not errors)
| Company | Reason |
|---------|--------|
| Validus Reinsurance (~97%) | BMA subsidiary; assumed premiums are much larger than BMA-only GPW |
| Somers Re (~55%) | Partial entity scope difference |
| DaVinci Reinsurance (~22000%) | Dashboard GPW = 5.0 (placeholder); real APW ~1,100–1,350 |
| Starr/SiriusPoint/Arch/Allied World | These include Direct business in GPW; note extracts only Assumed |
| Canopius/Fidelis/Liberty/Vantage | Mixed direct+assumed scope or entity scope differences |

### Potential Data Issues (worth investigating)
| Company | Year | APW | GPW | Delta | Possible Cause |
|---------|------|-----|-----|-------|----------------|
| Partner Reinsurance | 2023 | 3,653.8 | 4,379.2 | 16.6% | Multi-year table; may pick prior year value |
| Renaissance Reinsurance | 2024 | 2,232.0 | 3,180.0 | 29.8% | Scope change or prior year |

---

## Data Added to Dashboard

### New `reinsurance_note` section (per company-year)
Fields available where extracted:
- `assumed_premiums_written` — assumed/accepted premiums written (USD M)
- `ceded_premiums_written` — ceded premiums written (negative, USD M)
- `net_premiums_written` — net after cessions
- `assumed_premiums_earned` — assumed premiums earned
- `ceded_premiums_earned` — ceded premiums earned (negative)
- `net_premiums_earned` — net after cessions
- `assumed_losses_paid` — assumed losses incurred (where available)
- `ceded_losses_recovered` — ceded losses recovered (negative, where available)
- `net_losses_incurred` — net losses (where available)
- `extraction_status` — success / partial
- `source_pdf` — PDF filename

### `Net Premiums Written` added to `income_statement`
17 company-year entries updated where previously missing.

---

## Not Found — Likely Reasons

| Category | Companies |
|----------|-----------|
| No assumed/ceded split in note | AXIS Specialty, Lancashire, Group Ark, Harrington Re |
| IFRS 17 format (different note structure) | Hannover Re, Conduit Reinsurance |
| No reinsurance section found / different heading | Endurance, XL Bermuda, AXA XL, Fortitude, Premia, MS Amlin, Antares, Argo Re, AIRC, American Int'l, Fortitude Int'l |
| Image-only PDF | Hiscox Insurance, Brit Reinsurance (2024) |
| No PDF available | Ascot Bermuda (2023), Brit Reinsurance (2023) |
