import csv
import glob
import os
import re

RESULTS_DIR = "results"
OUTPUT_FILE = "results/extraction_results.csv"


def clean(value):
    value = value.replace("**", "")
    value = value.replace("*", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def get_metric_section(text, metric_names):

    for metric_name in metric_names:

        escaped = re.escape(metric_name)

        patterns = [

            # METRIC: REVENUE
            rf"METRIC\s*:\s*{escaped}.*?(?=METRIC\s*:|\Z)",

            # Metric: Total Revenue
            rf"Metric\s*:\s*{escaped}.*?(?=Metric\s*:|\Z)",

            # ## Metric 1: Total Revenue
            # ### Metric 1: Total Revenue
            rf"#+\s*Metric\s*\d*\s*:\s*{escaped}.*?(?=#+\s*Metric|\Z)",

            # ### 1. Total Revenue
            rf"#+\s*\d+\.?\s*{escaped}.*?(?=#+\s*\d+\.|\Z)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE | re.DOTALL
            )

            if match:
                return match.group(0)

    return None


def get_exact_amount(text, metric_names):

    section = get_metric_section(
        text,
        metric_names
    )

    if not section:
        return "Not reported in the filing"

    # Exact Amount can be followed by Unit on the same line
    # or on the next line.
    match = re.search(
        r"Exact Amount\s*:\s*(.*?)(?=\s+Unit\s*:|\s+Reporting Period\s*:|\s+Section/Table\s*:|\s+Section or Table\s*:|\s+Source\s*:|\n\s*---|\Z)",
        section,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return clean(match.group(1))

    return "Not reported in the filing"


def extract_revenue(text):

    return get_exact_amount(
        text,
        [
            "REVENUE",
            "Total Revenue"
        ]
    )


def extract_production(text):

    return get_exact_amount(
        text,
        [
            "PRODUCTION",
            "Total Production Volume",
            "Average Daily Production Volume"
        ]
    )


def extract_capex(text):

    return get_exact_amount(
        text,
        [
            "CAPEX",
            "Capital Expenditures"
        ]
    )


def process_file(filepath):

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as f:

        text = f.read()

    filing = os.path.basename(
        filepath
    ).replace(
        "_result.txt",
        ""
    )

    revenue = extract_revenue(text)
    production = extract_production(text)
    capex = extract_capex(text)

    return [
        filing,
        revenue,
        production,
        capex
    ]


def main():

    files = sorted(
        glob.glob(
            os.path.join(
                RESULTS_DIR,
                "*_result.txt"
            )
        )
    )

    if not files:

        print("ERROR: No result files found.")
        return

    rows = []

    for filepath in files:

        row = process_file(filepath)

        print("=" * 60)
        print()
        print(row[0])
        print()
        print("Revenue:", row[1])
        print()
        print("Production:", row[2])
        print()
        print("CapEx:", row[3])
        print()

        rows.append(row)

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Filing",
            "Revenue",
            "Production",
            "CapEx"
        ])

        writer.writerows(rows)

    print("=" * 60)
    print()
    print("DONE")
    print()
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()