from pathlib import Path
import os
from google import genai

# Connect to Gemini
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# The 15 SEC filings
filing_names = [
    "PR_10K_2025.txt",
    "PR_10Q_2026Q1.txt",
    "PR_10Q_2026Q2.txt",
    "FANG_10K_2025.txt",
    "FANG_10Q_2026Q1.txt",
    "FANG_10Q_2026Q2.txt",
    "CTRA_10K_2025.txt",
    "CTRA_10Q_2025Q3.txt",
    "CTRA_10Q_2026Q1.txt",
    "MTDR_10K_2025.txt",
    "MTDR_10Q_2025Q3.txt",
    "MTDR_10Q_2026Q1.txt",
    "SM_10K_2025.txt",
    "SM_10Q_2026Q1.txt",
    "SM_10Q_2026Q2.txt"
]

# Create results folder
results_folder = Path("results")
results_folder.mkdir(exist_ok=True)

# Process each filing
for filename in filing_names:

    file_path = Path(filename)

    print("\n" + "=" * 60)
    print(f"FILE: {file_path.stem.replace('_', ' ')}")
    print("=" * 60)

    if not file_path.exists():
        print(f"ERROR: {filename} was not found.")
        continue

    # Each filing gets its own results file
    result_file = results_folder / f"{file_path.stem}_result.txt"

    # Don't process a filing again if its result already exists
    if result_file.exists() and result_file.stat().st_size > 0:
        print(f"Already saved: {result_file}")
        continue

    try:
        # Read the SEC filing
        text = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        prompt = f"""
You are extracting financial information from an SEC 10-K filing.

Find the company's:

1. Total revenue for the fiscal year ended December 31, 2025
2. Average daily production volume for the fiscal year ended December 31, 2025
3. Capital expenditures for the fiscal year ended December 31, 2025

For each metric, return:

- Metric name
- Exact amount
- Unit/currency
- Fiscal year
- Section or table where you found it

Use the value reported in the filing.
Do not calculate or estimate a value unless necessary.

SEC filing:

{text}
"""

        print("Sending filing to Gemini...")

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        # SAVE IMMEDIATELY after Gemini responds
        result_file.write_text(
            response.text,
            encoding="utf-8"
        )

        print("RESULT:")
        print(response.text)
        print(f"Saved to: {result_file}")

    except Exception as e:
        print(f"ERROR processing {filename}:")
        print(e)
        print("Moving to the next filing...")

print("\n" + "=" * 60)
print("ALL FILINGS PROCESSED")
print("=" * 60)