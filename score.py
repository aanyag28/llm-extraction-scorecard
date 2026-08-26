import csv
import re
from pathlib import Path
from openpyxl import load_workbook


BASE_DIR = Path(__file__).resolve().parent

ANSWER_KEY = BASE_DIR / "answer_key" / "answer_key.csv-2.xlsx"
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_FILE = RESULTS_DIR / "detailed_results.csv"


# ==================================================
# LOAD ANSWER KEY
# ==================================================

workbook = load_workbook(
    ANSWER_KEY,
    data_only=True
)

sheet = workbook["Answer keys"]

headers = [cell.value for cell in sheet[1]]

answer_rows = []

for row in sheet.iter_rows(min_row=2, values_only=True):
    data = dict(zip(headers, row))

    if data.get("Filing") and data.get("Metric"):
        answer_rows.append(data)


# ==================================================
# FIND GEMINI RESULT FILE
# ==================================================

def find_gemini_file(ticker, filing):

    ticker = str(ticker).strip().upper()
    filing = str(filing).strip().upper()

    if "2025 10-K" in filing:
        filename = f"{ticker}_10K_2025_result.txt"

    elif "Q1 2026 10-Q" in filing:
        filename = f"{ticker}_10Q_2026Q1_result.txt"

    elif "Q2 2026 10-Q" in filing:
        filename = f"{ticker}_10Q_2026Q2_result.txt"

    elif "Q3 2025 10-Q" in filing:
        filename = f"{ticker}_10Q_2025Q3_result.txt"

    else:
        return None

    path = RESULTS_DIR / filename

    if path.exists():
        return path

    return None


# ==================================================
# FIND METRIC SECTION
# ==================================================

def get_metric_section(text, metric):

    metric = str(metric).strip().lower()

    # NEW GEMINI FORMAT:
    #
    # METRIC: REVENUE
    # Exact Amount: 7,645 million
    #
    # METRIC: PRODUCTION
    # ...

    pattern = (
        r"METRIC\s*:\s*"
        + re.escape(metric)
        + r"\b"
        r".*?"
        r"(?=METRIC\s*:|\Z)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(0)

    # OLD FORMAT:
    #
    # ### Metric 1: Total Revenue

    metric_number = {
        "revenue": "1",
        "production": "2",
        "capex": "3"
    }

    if metric not in metric_number:
        return ""

    number = metric_number[metric]

    names = {
        "revenue": r"(?:total\s+)?revenues?",
        "production": r"(?:total\s+)?production(?:\s+volume)?",
        "capex": r"(?:capital\s+)?expenditures?"
    }

    name_pattern = names[metric]

    pattern = (
        r"###\s*\**\s*Metric\s*"
        + number
        + r"\s*:\s*"
        + name_pattern
        + r".*?"
        r"(?=###\s*\**\s*Metric\s*[123]|\Z)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(0)

    # Another old format:
    #
    # ### 1. TOTAL REVENUE

    pattern = (
        r"###\s*\**\s*"
        + number
        + r"\s*[\.:]\s*"
        + name_pattern
        + r".*?"
        r"(?=###\s*\**\s*[123]\s*[\.:]|\Z)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(0)

    return ""


# ==================================================
# EXTRACT EXACT AMOUNT
# ==================================================

def extract_exact_amount(section):

    if not section:
        return "Not found"

    lines = section.splitlines()

    # Look for "Exact Amount:"
    for i, line in enumerate(lines):

        cleaned = (
            line
            .replace("**", "")
            .replace("*", "")
            .strip()
        )

        match = re.search(
            r"Exact\s+Amount\s*:\s*(.*)",
            cleaned,
            flags=re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            if value:
                return value

            # Value may be on next line
            for next_line in lines[i + 1:i + 5]:

                next_cleaned = (
                    next_line
                    .replace("**", "")
                    .replace("*", "")
                    .strip()
                )

                if re.search(r"\d", next_cleaned):
                    return next_cleaned

    # Production fallback
    match = re.search(
        r"TOTAL\s+PRODUCTION\s*=\s*([^\n]+)",
        section,
        flags=re.IGNORECASE
    )

    if match:
        return (
            "TOTAL PRODUCTION = "
            + match.group(1).strip()
        )

    return "Not found"


# ==================================================
# EXTRACT UNIT
# ==================================================

def extract_unit(section):

    if not section:
        return ""

    match = re.search(
        r"Unit\s*:\s*([^\n]+)",
        section,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    if re.search(r"\bMMBoe\b", section, re.IGNORECASE):
        return "MMBoe"

    if re.search(r"\bMBOE\b", section, re.IGNORECASE):
        return "MBOE"

    if re.search(r"\bMBOE/d\b", section, re.IGNORECASE):
        return "MBOE/d"

    if re.search(r"\bbillion\b", section, re.IGNORECASE):
        return "billion dollars"

    if re.search(r"\bmillion\b", section, re.IGNORECASE):
        return "million dollars"

    if re.search(r"\bthousand\b", section, re.IGNORECASE):
        return "thousand dollars"

    return ""


# ==================================================
# EXTRACT NUMBERS
# ==================================================

def extract_numbers(value):

    if value is None:
        return []

    text = str(value)

    text = text.replace(",", "")

    matches = re.findall(
        r"-?\d+(?:\.\d+)?",
        text
    )

    return [float(x) for x in matches]


# ==================================================
# DETERMINE UNIT NEAR A NUMBER
# ==================================================

def get_number_unit(text, number):

    text = str(text)

    clean_text = text.replace(",", "")

    number_text = str(number)

    # For integers such as 7645.0, also try 7645
    if number_text.endswith(".0"):
        number_text = number_text[:-2]

    position = clean_text.find(number_text)

    if position == -1:
        return ""

    start = max(0, position - 50)
    end = min(
        len(clean_text),
        position + len(number_text) + 80
    )

    context = clean_text[start:end].lower()

    if "billion" in context:
        return "billion dollars"

    if "million" in context:
        return "million dollars"

    if "thousand" in context:
        return "thousand dollars"

    if "mmboe" in context:
        return "MMBoe"

    if "mboe/d" in context:
        return "MBOE/d"

    if "mboe" in context:
        return "MBOE"

    return ""


# ==================================================
# NORMALIZE UNIT
# ==================================================

def normalize_unit(unit):

    if unit is None:
        return ""

    unit = str(unit).lower().strip()

    if "billion" in unit:
        return "billion"

    if "million" in unit:
        return "million"

    if "thousand" in unit:
        return "thousand"

    if "mmboe" in unit:
        return "mmboe"

    if "mboe/d" in unit:
        return "mboe/d"

    if "mboe" in unit:
        return "mboe"

    return unit


# ==================================================
# CONVERT VALUES
# ==================================================

def convert_value(value, from_unit, to_unit):

    if value is None:
        return None

    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)

    # Money conversions

    if source == "billion" and target == "million":
        return value * 1000

    if source == "billion" and target == "thousand":
        return value * 1000000

    if source == "million" and target == "billion":
        return value / 1000

    if source == "million" and target == "thousand":
        return value * 1000

    if source == "thousand" and target == "million":
        return value / 1000

    if source == "thousand" and target == "billion":
        return value / 1000000

    # Production conversions

    if source == "mmboe" and target == "mboe":
        return value * 1000

    if source == "mboe" and target == "mmboe":
        return value / 1000

    return value


# ==================================================
# SCORE ROW
# ==================================================

def score_row(
    extracted_value,
    extracted_unit,
    answer_value,
    answer_unit,
    metric
):

    if not extracted_value:
        return False

    if str(extracted_value).lower() == "not found":
        return False

    extracted_numbers = extract_numbers(
        extracted_value
    )

    answer_numbers = extract_numbers(
        answer_value
    )

    if not extracted_numbers:
        return False

    if not answer_numbers:
        return False

    answer_number = answer_numbers[0]

    metric = str(metric).strip().lower()

    answer_unit_normalized = normalize_unit(
        answer_unit
    )

    # ==================================================
    # PRODUCTION
    # ==================================================

    if metric == "production":

        for number in extracted_numbers:

            local_unit = get_number_unit(
                extracted_value,
                number
            )

            if not local_unit:
                local_unit = extracted_unit

            local_unit_normalized = normalize_unit(
                local_unit
            )

            # Do NOT accept daily production
            if local_unit_normalized == "mboe/d":
                continue

            converted = convert_value(
                number,
                local_unit_normalized,
                answer_unit_normalized
            )

            if converted is not None:

                if abs(
                    converted - answer_number
                ) < 0.01:

                    return True

        return False

    # ==================================================
    # REVENUE / CAPEX
    # ==================================================

    for number in extracted_numbers:

        local_unit = get_number_unit(
            extracted_value,
            number
        )

        if not local_unit:
            local_unit = extracted_unit

        local_unit_normalized = normalize_unit(
            local_unit
        )

        converted = convert_value(
            number,
            local_unit_normalized,
            answer_unit_normalized
        )

        if converted is not None:

            if abs(
                converted - answer_number
            ) < 0.01:

                return True

    return False


# ==================================================
# PROCESS EVERY ANSWER KEY ROW
# ==================================================

detailed_rows = []

for answer in answer_rows:

    ticker = str(
        answer["Ticker"]
    ).strip()

    filing = str(
        answer["Filing"]
    ).strip()

    metric = str(
        answer["Metric"]
    ).strip()

    answer_value = answer["Value"]
    answer_unit = answer["Unit"]

    gemini_file = find_gemini_file(
        ticker,
        filing
    )

    if gemini_file is None:

        extracted_value = "Gemini result not found"
        extracted_unit = ""
        correct = False

    else:

        text = gemini_file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        section = get_metric_section(
            text,
            metric
        )

        extracted_value = extract_exact_amount(
            section
        )

        extracted_unit = extract_unit(
            section
        )

        correct = score_row(
            extracted_value,
            extracted_unit,
            answer_value,
            answer_unit,
            metric
        )

    detailed_rows.append({
        "Filing": filing,
        "Ticker": ticker,
        "Metric": metric,
        "Gemini Extracted Value": extracted_value,
        "Gemini Unit": extracted_unit,
        "Answer Key Value": answer_value,
        "Answer Key Unit": answer_unit,
        "Correct": "Correct" if correct else "Incorrect"
    })


# ==================================================
# SAVE CSV
# ==================================================

RESULTS_DIR.mkdir(
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Filing",
            "Ticker",
            "Metric",
            "Gemini Extracted Value",
            "Gemini Unit",
            "Answer Key Value",
            "Answer Key Unit",
            "Correct"
        ]
    )

    writer.writeheader()
    writer.writerows(detailed_rows)


# ==================================================
# SCORE SUMMARY
# ==================================================

def rows_for(metric):

    return [
        row
        for row in detailed_rows
        if row["Metric"].lower()
        == metric.lower()
    ]


def count_correct(rows):

    return sum(
        row["Correct"] == "Correct"
        for row in rows
    )


def pct(rows):

    if not rows:
        return 0.0

    return (
        count_correct(rows)
        / len(rows)
        * 100
    )


revenue_rows = rows_for("Revenue")
production_rows = rows_for("Production")
capex_rows = rows_for("CapEx")

total = len(detailed_rows)

correct_total = sum(
    row["Correct"] == "Correct"
    for row in detailed_rows
)


# ==================================================
# PRINT
# ==================================================

print()

print("====================================")
print("GEMINI EXTRACTION SCORE")
print("====================================")

print(
    f"Revenue:     "
    f"{count_correct(revenue_rows)}/"
    f"{len(revenue_rows)} "
    f"({pct(revenue_rows):.1f}%)"
)

print(
    f"Production:  "
    f"{count_correct(production_rows)}/"
    f"{len(production_rows)} "
    f"({pct(production_rows):.1f}%)"
)

print(
    f"CapEx:       "
    f"{count_correct(capex_rows)}/"
    f"{len(capex_rows)} "
    f"({pct(capex_rows):.1f}%)"
)

if total:

    print(
        f"Overall:     "
        f"{correct_total}/"
        f"{total} "
        f"({correct_total / total * 100:.1f}%)"
    )

else:

    print(
        "Overall:     0/0 (0.0%)"
    )

print("====================================")

print()

print("Detailed results saved to:")

print(OUTPUT_FILE)