from pathlib import Path

from google import genai

# --------------------------------------------------
# SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# IMPORTANT:
# Replace YOUR_NEW_API_KEY with your newly regenerated Gemini API key.
client = genai.Client()

RESULTS_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# FIND FILINGS
# --------------------------------------------------

filing_files = sorted(
    BASE_DIR.glob("*.txt")
)

for file_path in filing_files:

    filename = file_path.stem

    # Skip unrelated files
    if filename in [
        "results",
        "results.txt"
    ]:
        continue

    # Only process SEC filing text files
    if not any(
        x in filename
        for x in ["10K", "10Q"]
    ):
        continue

    print()
    print("=" * 60)
    print(f"PROCESSING: {filename}")
    print("=" * 60)

    try:

        # --------------------------------------------------
        # READ FILING
        # --------------------------------------------------

        text = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

        prompt = f"""
You are a financial data extraction system analyzing ONE SEC filing.

Extract THREE metrics for the reporting period covered by THIS filing:

1. TOTAL REVENUE
2. TOTAL PRODUCTION VOLUME
3. CAPITAL EXPENDITURES

IMPORTANT:

SEC filing text may have damaged table formatting because the filing
was converted from HTML/PDF into plain text.

Numbers may not appear directly beside their labels.

DO NOT say "Not reported in the filing" just because a table looks
incomplete.

Before declaring a metric unavailable, search the ENTIRE filing and
check equivalent terminology.

==================================================
REVENUE
==================================================

Find the company's TOTAL revenue for the reporting period.

Look for:

- Total revenues
- Total revenue
- Total operating revenues
- Total operating revenues and other income
- Total revenues and other income
- Oil and gas sales
- Other equivalent total-revenue labels

If a detailed revenue table contains a clearly reported total,
use that total.

IMPORTANT:

Do not confuse quarterly revenue with six-month revenue.

Use the period specifically requested by the filing's reporting period.

==================================================
PRODUCTION
==================================================

Find TOTAL production volume for the reporting period.

Look especially for:

- Total (MBOE)
- Total (MBoe)
- Total oil equivalent (MBOE)
- Oil equivalent (MBOE)
- Equivalents (MMBOE)
- Total production
- Total production volume

DO NOT report:

- average daily production
- BOE/d
- MBOE/d
- barrels per day
- daily production

If the filing directly reports total production in MBOE,
use that value.

Do NOT calculate production from daily production if a total
production value is available.

The final production answer MUST be total MBOE.

==================================================
CAPITAL EXPENDITURES
==================================================

Find TOTAL capital expenditures for the reporting period.

Search for:

- Capital expenditures
- Capital expenditure activities
- Total capital expenditures
- Additions to oil and gas properties
- Additions to oil and natural gas properties
- Drilling and development capital expenditures
- Drilling, completion and equipping capital expenditures
- Capital expenditures for drilling, completion and other fixed asset additions

Check all of these areas:

- Consolidated Statements of Cash Flows
- Condensed Consolidated Statements of Cash Flows
- MD&A
- Results of Operations
- Capital Expenditure Activities
- tables discussing capital spending
- financial highlights

If a capital expenditure amount is shown in parentheses
because it is a cash outflow, report the POSITIVE amount.

Example:

($1,929 million) = 1,929 million dollars

IMPORTANT:

Do not confuse:

- capital expenditures
- acquisitions
- purchases of investments
- total investing cash flow
- depreciation
- capital expenditures incurred vs. paid

Use the value that represents the company's reported capital
expenditures for the requested reporting period.

==================================================
REPORTING PERIOD
==================================================

Determine the actual reporting period from THIS filing.

Examples:

Annual 10-K:
Fiscal year ended December 31, 2025

Q1 10-Q:
Three months ended March 31, 2026

Q2 10-Q:
Three months ended June 30, 2026

Do NOT automatically use the annual period.

For quarterly filings, pay attention to whether a table contains:

- three-month values
- six-month values

Use the value for the reporting period requested by the filing.

==================================================
VERY IMPORTANT SEARCH RULE
==================================================

Do not give up after finding one keyword.

If you find:

"capital expenditures"

but the number is missing because of broken table formatting,
search the rest of the filing for:

- capital expenditure activities
- drilling and development
- additions to oil and gas properties
- total capital expenditures
- financial highlights

Likewise, if "total revenues" appears without a visible number,
search for the same revenue total in:

- Results of Operations
- MD&A
- financial highlights
- operating data
- statements of operations

For production, search for "MBOE", "MBoe", "oil equivalent",
and "total production".

Only report "Not reported in the filing" AFTER checking the
entire filing.

==================================================
OUTPUT FORMAT
==================================================

Return exactly these three sections:

METRIC: REVENUE
Exact Amount:
Unit:
Reporting Period:
Section/Table:
Source:

METRIC: PRODUCTION
Exact Amount:
Unit:
Reporting Period:
Section/Table:
Source:

METRIC: CAPEX
Exact Amount:
Unit:
Reporting Period:
Section/Table:
Source:

Production MUST be total MBOE.

Do not include average daily production as the production answer.

Do not invent values.

SEC FILING:

{text}
"""

        print("Sending filing to Gemini...")

        # --------------------------------------------------
        # SEND TO GEMINI
        # --------------------------------------------------

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        result_file = RESULTS_DIR / f"{filename}_result.txt"

        result_file.write_text(
            response.text,
            encoding="utf-8"
        )

        print("RESULT:")
        print(response.text)

        print()
        print(f"Saved to: {result_file}")

    except Exception as e:

        print()
        print(f"ERROR processing {filename}:")
        print(e)
        print("Moving to the next filing...")

# --------------------------------------------------
# FINISHED
# --------------------------------------------------

print()
print("=" * 60)
print("ALL FILINGS PROCESSED")
print("=" * 60)
