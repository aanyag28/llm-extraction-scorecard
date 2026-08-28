from pathlib import Path
import time

from google import genai

# --------------------------------------------------
# SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

client = genai.Client()

RESULTS_DIR.mkdir(exist_ok=True)

# Wait between requests so we don't hit Gemini's free-tier
# input-token-per-minute quota.
WAIT_BETWEEN_REQUESTS = 40

# How many times to retry after a 429 quota error.
MAX_RETRIES = 3


# --------------------------------------------------
# PROMPT
# --------------------------------------------------

PROMPT_TEMPLATE = """
You are a financial data extraction system analyzing ONE SEC filing.

Extract exactly THREE metrics from THIS filing:

1. TOTAL REVENUE
2. TOTAL PRODUCTION VOLUME
3. CAPITAL EXPENDITURES

The filing is plain text converted from an SEC HTML/PDF filing.
Tables may have broken formatting. Labels and numbers may be
separated by many lines.

You MUST search the ENTIRE filing before deciding that something
is unavailable.

==================================================
REPORTING PERIOD
==================================================

First determine the reporting period.

For a 10-K:
Use the fiscal-year value.

For a quarterly 10-Q:
Use the THREE-MONTH value for that quarter, NOT the six-month
or nine-month cumulative value.

Examples:

Q1 2026 = three months ended March 31, 2026
Q2 2026 = three months ended June 30, 2026
Q3 2025 = three months ended September 30, 2025

==================================================
REVENUE
==================================================

Find TOTAL REVENUE for the reporting period.

Search for:

- Total revenue
- Total revenues
- Total operating revenues
- Total operating revenues and other income
- Total revenues and other income
- Revenue
- Revenues
- Oil, gas and NGL production revenue
- Oil and gas sales
- Statements of Operations
- Statements of Income
- MD&A revenue tables

Choose the company's TOTAL revenue measure.

Do not choose an individual revenue component if a total exists.

For a quarterly filing, use the three-month value.

If a table has both three-month and year-to-date values, use the
three-month value.

==================================================
PRODUCTION
==================================================

Find TOTAL PRODUCTION VOLUME for the reporting period.

Search the ENTIRE filing for:

- Total production
- Total production volume
- Total MBOE
- Total MBoe
- Total oil equivalent
- MBOE
- MBoe
- MMBOE
- Production Data
- Production Results
- Operating Data
- Results of Operations

The answer MUST be total MBOE.

DO NOT use:

- BOE/d
- MBOE/d
- barrels per day
- average daily production
- average production per day

If the filing gives production in MMBOE:

72.2 MMBOE = 72,200 MBOE
69.4 MMBOE = 69,400 MBOE
40.0 MMBOE = 40,000 MBOE

If the filing directly gives total MBOE, use that value.

Do NOT calculate from daily production if total production is
available.

For quarterly filings, use the three-month production value.

==================================================
CAPITAL EXPENDITURES
==================================================

Find TOTAL CAPITAL EXPENDITURES for the reporting period.

Search the ENTIRE filing for:

- Capital expenditures
- Capital expenditure
- Total capital expenditures
- Capital expenditure activities
- Capital spending
- Capital investments
- Drilling and development capital expenditures
- Drilling, completion and equipping capital expenditures
- Drilling, completion and other fixed asset additions
- Additions to oil and gas properties
- Additions to oil and natural gas properties
- Purchases of property and equipment
- Capital expenditures incurred
- Capital expenditures paid
- Cash capital expenditures

Check:

- Statements of Cash Flows
- Condensed Statements of Cash Flows
- MD&A
- Results of Operations
- Capital Expenditure Activities
- financial highlights
- operating highlights
- capital spending tables

==================================================
CAPEX SELECTION
==================================================

Choose the value that represents TOTAL CAPITAL EXPENDITURES for
the requested reporting period.

Prefer an explicitly reported:

"Total capital expenditures"

or

"Capital expenditures"

amount.

Do NOT use:

- acquisitions
- business combinations
- purchases of investments
- total investing cash flow
- depreciation
- depletion
- amortization
- future guidance
- unrelated investing activities

If capital expenditures are divided into components such as:

- drilling/development
- midstream
- other property/equipment

and the filing clearly provides a total, use the total.

If no total is explicitly provided, add components ONLY when the
components clearly represent all capital expenditures for the
same reporting period.

For quarterly filings, use the THREE-MONTH amount.

Example:

Three months = $996 million
Six months = $1,929 million

Answer:

996 million dollars

If a cash-flow amount is shown in parentheses, report it as a
positive amount.

Example:

($1,929 million) -> 1,929 million dollars

==================================================
DAMAGED TABLES
==================================================

The plain-text conversion may separate labels from values.

Do not conclude "Not found" merely because the first table is
broken.

Search the entire filing and use surrounding text to reconstruct
the table.

For example, if "capital expenditures" appears without an
immediately adjacent number, search for the same amount elsewhere
in the filing.

==================================================
IMPORTANT
==================================================

Only use information from THIS filing.

Do not use information from another filing.

Do not use information from another company.

Do not invent or estimate values.

Production MUST be total MBOE.

Quarterly filings MUST use the three-month value.

==================================================
OUTPUT
==================================================

Return EXACTLY this format:

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

SEC FILING:

{filing_text}
"""


# --------------------------------------------------
# FIND FILINGS
# --------------------------------------------------

filing_files = sorted(BASE_DIR.glob("*.txt"))

processed_any = False

for file_path in filing_files:

    filename = file_path.stem

    # --------------------------------------------------
    # SKIP UNRELATED FILES
    # --------------------------------------------------

    if filename in ["results", "results.txt"]:
        continue

    if not any(x in filename for x in ["10K", "10Q"]):
        continue

    # --------------------------------------------------
    # SKIP FILINGS THAT ALREADY HAVE RESULTS
    # --------------------------------------------------

    result_file = RESULTS_DIR / f"{filename}_result.txt"

    if result_file.exists():
        print()
        print("=" * 60)
        print(f"SKIPPING: {filename}")
        print("Result file already exists.")
        print("=" * 60)
        continue

    processed_any = True

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

        print(f"Filing size: {len(text):,} characters")
        print("Sending filing to Gemini...")

        prompt = PROMPT_TEMPLATE.format(
            filing_text=text
        )

        # --------------------------------------------------
        # SEND TO GEMINI
        # --------------------------------------------------

        response = None

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                break

            except Exception as e:

                error_text = str(e)

                # ------------------------------------------
                # HANDLE QUOTA ERROR
                # ------------------------------------------

                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

                    if attempt < MAX_RETRIES:

                        print()
                        print(
                            f"Gemini quota reached. "
                            f"Waiting 45 seconds before retry "
                            f"({attempt}/{MAX_RETRIES})..."
                        )

                        time.sleep(45)

                    else:

                        print()
                        print(
                            "Quota still unavailable after "
                            f"{MAX_RETRIES} attempts."
                        )

                        raise

                else:

                    raise

        # --------------------------------------------------
        # CHECK RESPONSE
        # --------------------------------------------------

        if response is None:
            raise RuntimeError("Gemini returned no response.")

        result_text = response.text

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        result_file.write_text(
            result_text,
            encoding="utf-8"
        )

        print()
        print("RESULT:")
        print(result_text)

        print()
        print(f"Saved to: {result_file}")

        # --------------------------------------------------
        # WAIT BEFORE NEXT FILING
        # --------------------------------------------------

        print()
        print(
            f"Waiting {WAIT_BETWEEN_REQUESTS} seconds "
            "before the next filing..."
        )

        time.sleep(WAIT_BETWEEN_REQUESTS)

    except Exception as e:

        print()
        print(f"ERROR processing {filename}:")
        print(e)
        print("Moving to the next filing...")

        # Give Gemini some breathing room after an error.
        print("Waiting 45 seconds before continuing...")
        time.sleep(45)


# --------------------------------------------------
# FINISHED
# --------------------------------------------------

print()
print("=" * 60)

if processed_any:
    print("ALL NEW FILINGS PROCESSED")
else:
    print("NO NEW FILINGS TO PROCESS")

print("=" * 60)