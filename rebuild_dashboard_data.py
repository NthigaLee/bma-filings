#!/usr/bin/env python3
"""
Rebuild dashboard_data.json from knowledge_base.json with accurate PDF-extracted values.
Detects per-company reporting units (thousands vs millions) and normalises to millions.
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# ── Name mapping: dashboard short name → KB prefix ──────────────────────────
NAME_MAP = {
    "Arch Reinsurance": "Arch Reinsurance Ltd.",
    "Ascot Bermuda": "Ascot Bermuda Limited",
    "Aspen Bermuda": "Aspen Bermuda Limited",
    "AXIS Specialty": "AXIS Specialty Limited",
    "Chubb Tempest Reinsurance": "Chubb Tempest Reinsurance Ltd.",
    "Everest Reinsurance Bermuda": "Everest Reinsurance Bermuda Ltd.",
    "Hannover Re Bermuda": "Hannover Re Bermuda Ltd.",
    "Markel Bermuda": "Markel Bermuda Limited",
    "Partner Reinsurance Company": "Partner Reinsurance Company Ltd.",
    "Renaissance Reinsurance": "Renaissance Reinsurance Ltd.",
    "Endurance Specialty Insurance": "Endurance Specialty Insurance Ltd.",
    "XL Bermuda": "XL Bermuda Ltd",
    "AXA XL Reinsurance": "AXA XL Reinsurance Ltd",
    "Validus Reinsurance": "Validus Reinsurance Ltd.",
    "Somers Re": "Somers Re Ltd.",
    "Lancashire Insurance Company": "Lancashire Insurance Company Limited",
    "Hiscox Insurance Company Bermuda": "Hiscox Insurance Company Bermuda Limited",
    "Canopius Reinsurance": "Canopius Reinsurance Limited",
    "Conduit Reinsurance": "Conduit Reinsurance Limited",
    "Fidelis Insurance Bermuda": "Fidelis Insurance Bermuda Limited",
    "Fortitude Reinsurance Company": "Fortitude Reinsurance Company Ltd.",
    "Group Ark Insurance": "Group Ark Insurance Limited",
    "Hamilton Re": "Hamilton Re Ltd.",
    "Harrington Re": "Harrington Re Ltd.",
    "Liberty Specialty Markets Bermuda": "Liberty Specialty Markets Bermuda Limited",
    "MS Amlin AG": "MS Amlin AG",
    "Premia Reinsurance": "Premia Reinsurance Ltd.",
    "Starr Insurance & Reinsurance": "Starr Insurance  Reinsurance Limited",
    "Vantage Risk": "Vantage Risk Ltd.",
    "SiriusPoint Bermuda Insurance": "SiriusPoint Bermuda Insurance Company Ltd.",
    "ABR Reinsurance Ltd.": "ABR Reinsurance Ltd.",
    "Allied World Assurance Company Ltd": "Allied World Assurance Company Ltd.",
    "American International Reinsurance Company Ltd.": "American International Reinsurance Company Ltd.",
    "Antares Reinsurance Company Limited": "Antares Reinsurance Company Limited",
    "Argo Re Ltd.": "Argo Re Ltd.",
    "Brit Reinsurance Bermuda Limited": "Brit Reinsurance Bermuda Limited",
    "Convex Re Limited": "Convex Re Limited",
    "DaVinci Reinsurance Ltd.": "DaVinci Reinsurance Ltd.",
    "Everest International Reinsurance Ltd.": "Everest International Reinsurance Ltd.",
    "Fortitude International Reinsurance Ltd.": "Fortitude International Reinsurance Ltd.",
}

# ── Balance sheet KB label → dashboard label ────────────────────────────────
BS_MAP = {
    "Total Assets": "Total Assets",
    "Total Liabilities": "Total Liabilities",
    "Total Shareholders Equity": "Total Equity",
    "Cash and Cash Equivalents": "Cash and Cash Equivalents",
    "Total Investments": "Total Investments",
    "Loss Reserves": "Loss Reserves",
    "Claims Reserves": "Loss Reserves",           # alias
    "Loss and LAE Reserves": "Loss Reserves",     # alias
    "Insurance Contract Liabilities": "Loss Reserves",  # alias
    "Unearned Premiums": "Unearned Premiums",
    "Fixed Income Investments": "Fixed Maturities - AFS",
    "Equity Investments": "Equity Securities",
}

# ── Income statement KB label → dashboard label ─────────────────────────────
IS_MAP = {
    "Net Premiums Earned": "Net Premiums Earned",
    "Net Premiums Written": "Net Premiums Written",
    "Net Investment Income": "Net Investment Income",
    "Total Revenues": "Total Revenues",
    "Net Income": "Net Income",
    "Net Loss": "Net Income",                   # alias (negative)
    "Total Expenses": "Total Expenses",
    "Net Claims": "Net Claims and Benefits",
    "Claims and Benefits": "Net Claims and Benefits",
    "Net Underwriting Result": "Net Underwriting Result",
    "Combined Ratio": "Combined Ratio",
}


def detect_unit_multiplier(company_data: dict) -> float:
    """Return 1.0 if values are in millions, 0.001 if in thousands."""
    bs = company_data.get("balance_sheet", {})
    total_assets = bs.get("Total Assets", {}).get("value", 0) or 0
    # Heuristic: Class 4 companies have ≥$100M total assets.
    # If raw value > 500_000 it almost certainly represents thousands.
    if total_assets > 500_000:
        return 0.001
    return 1.0


def get_kb_entry(kb_companies: dict, kb_prefix: str, year: int):
    """Find KB entry matching prefix and year."""
    key = f"{kb_prefix} {year}"
    if key in kb_companies:
        return kb_companies[key]
    # Fuzzy: try stripping trailing punctuation variants
    for k in kb_companies:
        if str(year) in k and k.replace(",", "").startswith(kb_prefix.rstrip(".")):
            return kb_companies[k]
    return None


# Aliases: try these labels in order when primary not found
LABEL_ALIASES = {
    "Loss Reserves": ["Loss and LAE Reserves", "Claims Reserves", "Insurance Contract Liabilities", "Policy Reserves"],
    "Net Claims": ["Net Claims and Claim Expenses", "Claims and Benefits", "Net Claims and Benefits", "Loss and LAE"],
    "Net Income": ["Net Loss", "Net Earnings", "Net Profit (Loss)"],
    "Total Shareholders Equity": ["Total Stockholders Equity", "Total Equity"],
    "Fixed Income Investments": ["Fixed Maturities", "Fixed Maturity Securities", "Fixed Income Securities"],
}


def extract_value(entry, label):
    """Get numeric value from KB entry, trying aliases if primary label not found."""
    candidates = [label] + LABEL_ALIASES.get(label, [])
    for candidate in candidates:
        for section in ("balance_sheet", "income_statement"):
            item = entry.get(section, {}).get(candidate, {})
            if isinstance(item, dict) and item.get("value") is not None:
                return item["value"]
    return None


def build_metric_dict(companies, kb_companies, year, kb_label, dash_label):
    """Build {company: value_in_millions} for one metric/year."""
    result = {}
    for dash_name, kb_prefix in NAME_MAP.items():
        entry = get_kb_entry(kb_companies, kb_prefix, year)
        if entry:
            raw = extract_value(entry, kb_label)
            if raw is not None and raw != 0:
                mult = detect_unit_multiplier(entry)
                result[dash_name] = round(raw * mult, 1)
            else:
                result[dash_name] = 0
        else:
            result[dash_name] = 0
    return result


def main():
    with open("data/knowledge_base.json") as f:
        kb = json.load(f)
    kb_companies = kb["companies"]

    companies_list = list(NAME_MAP.keys())
    # Expand years to full range available in KB
    all_years = sorted({
        int(y) for k in kb_companies for y in [k.split()[-1]]
        if y.isdigit() and 2019 <= int(y) <= 2025
    })

    print(f"Building dashboard data for years: {all_years}")
    print(f"Companies: {len(companies_list)}")

    data = {}
    for year in all_years:
        year_str = str(year)
        data[year_str] = {"balance_sheet": {}, "income_statement": {}}

        # Balance sheet metrics
        bs_labels = [
            ("Fixed Income Investments", "Fixed Maturities - AFS"),
            ("Equity Investments", "Equity Securities"),
            ("Total Investments", "Total Investments"),
            ("Cash and Cash Equivalents", "Cash and Cash Equivalents"),
            ("Total Assets", "Total Assets"),
            ("Loss Reserves", "Loss Reserves"),
            ("Unearned Premiums", "Unearned Premiums"),
            ("Total Liabilities", "Total Liabilities"),
            ("Total Shareholders Equity", "Total Equity"),
        ]
        for kb_label, dash_label in bs_labels:
            data[year_str]["balance_sheet"][dash_label] = build_metric_dict(
                companies_list, kb_companies, year, kb_label, dash_label
            )

        # Income statement metrics
        is_labels = [
            ("Net Premiums Written", "Net Premiums Written"),
            ("Net Premiums Earned", "Net Premiums Earned"),
            ("Net Investment Income", "Net Investment Income"),
            ("Total Revenues", "Total Revenues"),
            ("Net Claims", "Net Claims and Benefits"),
            ("Total Expenses", "Total Expenses"),
            ("Net Income", "Net Income"),
        ]
        for kb_label, dash_label in is_labels:
            data[year_str]["income_statement"][dash_label] = build_metric_dict(
                companies_list, kb_companies, year, kb_label, dash_label
            )

    # Count coverage
    total_cells = 0
    filled_cells = 0
    for yr_data in data.values():
        for section in yr_data.values():
            for metric_data in section.values():
                for v in metric_data.values():
                    total_cells += 1
                    if v and v != 0:
                        filled_cells += 1

    coverage = filled_cells / total_cells * 100 if total_cells else 0
    print(f"Data coverage: {filled_cells}/{total_cells} cells ({coverage:.1f}%)")

    output = {
        "companies": companies_list,
        "years": all_years,
        "data": data,
        "data_pending": False,
        "data_sourced": "PDF financial statements (pdfplumber extraction)",
        "last_updated": "2026-03-28",
    }

    with open("dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("Saved: dashboard_data.json")

    # Also write as JS variable for the site
    with open("dashboard_data.js", "w", encoding="utf-8") as f:
        f.write("const dashboardData = ")
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write(";\n")
    print("Saved: dashboard_data.js")

    # Quick spot-check
    print("\nSpot-check Endurance Specialty Insurance Total Assets:")
    for yr in ["2022", "2023", "2024"]:
        if yr in data:
            val = data[yr]["balance_sheet"]["Total Assets"].get("Endurance Specialty Insurance", 0)
            print(f"  {yr}: {val}M")


if __name__ == "__main__":
    main()
