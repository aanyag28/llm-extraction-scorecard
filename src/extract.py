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

# Save each filing's result separately
for filename in filing_names:

    file_path = Path(filename)

    print("\n" + "=" * 60)
    print(f"FILE: {file_path.stem.replace('_', ' ')}")
    print("=" * 60)

    if not file_path.exists():
        print(f"ERROR: {filename} was not found.")
        continue

    # Create a separate result file for this filing
    result_file = results_folder / f"{file_path.stem}_result.txt"

    # Skip a filing if we already successfully saved its result
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
You are extracting financial information from an SEC filing.

Find these three financial metrics:

1. Total revenue
2. Average daily production volume
3. Capital expenditures

For each metric, return:

- Metric name
- Exact amount
- Unit
- Fiscal year
- Section or table where you found it

Use the value reported in the filing.
Do not calculate or estimate a value unless the filing
explicitly requires it.

SEC filing:

{text}
"""

        print("Sending filing to Gemini...")

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        # Save the result IMMEDIATELY
        result_file.write_text(
            response.text,
            encoding="utf-8"
        )

        print("RESULT:")
        print(response.text)
        print(f"\nSaved to: {result_file}")

    except Exception as e:
        print(f"ERROR processing {filename}:")
        print(e)
        print("Moving to the next filing...")

print("\n" + "=" * 60)
print("ALL FILINGS PROCESSED")
print("=" * 60)
