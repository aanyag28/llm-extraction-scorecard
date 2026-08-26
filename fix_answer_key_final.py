from openpyxl import load_workbook
from pathlib import Path

BASE_DIR = Path.home() / "Documents" / "LLM-Extraction-Scorecard"
ANSWER_KEY = BASE_DIR / "answer_key" / "answer_key.csv-2.xlsx"

workbook = load_workbook(ANSWER_KEY)
sheet = workbook["Answer keys"]

# Find columns from the header row
headers = {}

for cell in sheet[1]:
    if cell.value is not None:
        headers[str(cell.value).strip()] = cell.column

ticker_col = headers["Ticker"]
filing_col = headers["Filing"]
metric_col = headers["Metric"]
value_col = headers["Value"]
unit_col = headers["Unit"]

# ============================================================
# VERIFIED PRODUCTION VALUES
# ALL PRODUCTION VALUES ARE TOTAL MBOE
# ============================================================

production = {
    ("FANG", "2025 10-K"): 336178,
    ("FANG", "Q1 2026 10-Q"): 88142,
    ("FANG", "Q2 2026 10-Q"): 92607,

    ("PR", "2025 10-K"): 143311,
    ("PR", "Q1 2026 10-Q"): 37156,
    ("PR", "Q2 2026 10-Q"): 34253,

    ("MTDR", "2025 10-K"): 75581,
    ("MTDR", "Q3 2025 10-Q"): 19245,
    ("MTDR", "Q1 2026 10-Q"): 18683,

    ("CTRA", "2025 10-K"): 285576,
    ("CTRA", "Q3 2025 10-Q"): 72200,
    ("CTRA", "Q1 2026 10-Q"): 69400,

    ("SM", "2025 10-K"): 75500,
    ("SM", "Q1 2026 10-Q"): 33400,
    ("SM", "Q2 2026 10-Q"): 40000,
}

# ============================================================
# ANSWER KEY VALUES WE ALREADY HAVE FROM YOUR SOURCE DATA
# ============================================================

values = {

    # ---------------- FANG ----------------

    ("FANG", "2025 10-K", "Revenue"):
        (15026, "million dollars"),

    ("FANG", "2025 10-K", "CapEx"):
        (3523, "million dollars"),

    ("FANG", "Q1 2026 10-Q", "Revenue"):
        (4240, "million dollars"),

    ("FANG", "Q1 2026 10-Q", "CapEx"):
        (933, "million dollars"),

    ("FANG", "Q2 2026 10-Q", "Revenue"):
        (5562, "million dollars"),

    ("FANG", "Q2 2026 10-Q", "CapEx"):
        (1929, "million dollars"),

    # ---------------- PR ----------------

    ("PR", "2025 10-K", "Revenue"):
        (5065211, "thousand dollars"),

    ("PR", "2025 10-K", "CapEx"):
        (1965926, "thousand dollars"),

    ("PR", "Q1 2026 10-Q", "Revenue"):
        (1388146, "thousand dollars"),

    ("PR", "Q1 2026 10-Q", "CapEx"):
        (466230, "thousand dollars"),

    ("PR", "Q2 2026 10-Q", "Revenue"):
        (1858035, "thousand dollars"),

    ("PR", "Q2 2026 10-Q", "CapEx"):
        (987664, "thousand dollars"),

    # ---------------- MTDR ----------------

    ("MTDR", "2025 10-K", "Revenue"):
        (3696277, "thousand dollars"),

    ("MTDR", "2025 10-K", "CapEx"):
        (1542253, "thousand dollars"),

    ("MTDR", "Q3 2025 10-Q", "Revenue"):
        (939015, "thousand dollars"),

    ("MTDR", "Q3 2025 10-Q", "CapEx"):
        (1093010, "thousand dollars"),

    ("MTDR", "Q1 2026 10-Q", "Revenue"):
        (671637, "thousand dollars"),

    ("MTDR", "Q1 2026 10-Q", "CapEx"):
        (377375, "thousand dollars"),

    # ---------------- CTRA ----------------

    ("CTRA", "2025 10-K", "Revenue"):
        (7645, "million dollars"),

    ("CTRA", "2025 10-K", "CapEx"):
        (2288, "million dollars"),

    ("CTRA", "Q3 2025 10-Q", "Revenue"):
        (1817, "million dollars"),

    ("CTRA", "Q3 2025 10-Q", "CapEx"):
        (1707, "million dollars"),

    ("CTRA", "Q1 2026 10-Q", "Revenue"):
        (1947, "million dollars"),

    ("CTRA", "Q1 2026 10-Q", "CapEx"):
        (655, "million dollars"),

    # ---------------- SM ----------------

    ("SM", "2025 10-K", "Revenue"):
        (3154, "million dollars"),

    ("SM", "2025 10-K", "CapEx"):
        (1438, "million dollars"),

    ("SM", "Q1 2026 10-Q", "Revenue"):
        (1479, "million dollars"),

    ("SM", "Q1 2026 10-Q", "CapEx"):
        (555, "million dollars"),

    ("SM", "Q2 2026 10-Q", "Revenue"):
        (2500, "million dollars"),

    ("SM", "Q2 2026 10-Q", "CapEx"):
        (1309, "million dollars"),
}


changed = 0

# ============================================================
# APPLY PRODUCTION VALUES
# ============================================================

for row in range(2, sheet.max_row + 1):

    ticker = sheet.cell(row, ticker_col).value
    filing = sheet.cell(row, filing_col).value
    metric = sheet.cell(row, metric_col).value

    if not ticker or not filing or not metric:
        continue

    ticker = str(ticker).strip().upper()
    filing = str(filing).strip()
    metric = str(metric).strip()

    # Fix trailing spaces in filings such as "2025 10-K "
    if metric.lower() == "production":

        key = (ticker, filing)

        if key in production:

            new_value = production[key]

            sheet.cell(row, value_col).value = new_value
            sheet.cell(row, unit_col).value = "MBOE"

            print(
                f"Production fixed: "
                f"{ticker} | {filing} | "
                f"{new_value} MBOE"
            )

            changed += 1

    # ========================================================
    # APPLY VERIFIED REVENUE / CAPEX VALUES
    # ========================================================

    key = (ticker, filing, metric)

    if key in values:

        new_value, new_unit = values[key]

        old_value = sheet.cell(row, value_col).value
        old_unit = sheet.cell(row, unit_col).value

        if old_value != new_value or old_unit != new_unit:

            sheet.cell(row, value_col).value = new_value
            sheet.cell(row, unit_col).value = new_unit

            print(
                f"Updated: "
                f"{ticker} | {filing} | {metric} | "
                f"{old_value} -> {new_value} | "
                f"{old_unit} -> {new_unit}"
            )

            changed += 1


# ============================================================
# SAVE
# ============================================================

workbook.save(ANSWER_KEY)

print()
print("====================================")
print("ANSWER KEY UPDATED")
print("====================================")
print(f"Cells/rows updated: {changed}")
print()
print("Saved to:")
print(ANSWER_KEY)
