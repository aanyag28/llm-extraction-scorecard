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

# Create the results folder
results_folder = Path("results")
results_folder.mkdir(exist_ok=True)

# Save everything in this file
output_file = results_folder / "extraction_results.txt"

with output_file.open("w", encoding="utf-8") as output:

    # Process each filing
    for filename in filing_names:

        file_path = Path(filename)

        print("\n" + "=" * 60)
        print(f"FILE: {file_path.stem.replace('_', ' ')}")
        print("=" * 60)

        output.write("\n" + "=" * 60 + "\n")
        output.write(f"FILE: {file_path.stem.replace('_', ' ')}\n")
        output.write("=" * 60 + "\n")

        if not file_path.exists():
            message = f"ERROR: {filename} was not found."
            print(message)
            output.write(message + "\n")
            continue

        try:
            # Read the filing
            text = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            # Prompt Gemini
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

            print("RESULT:")
            print(response.text)

            # Save the result
            output.write("RESULT:\n")
            output.write(response.text + "\n")

        except Exception as e:
            message = f"ERROR processing {filename}: {e}"
            print(message)
            print("Moving to the next filing...")
            output.write(message + "\n")

print("\n" + "=" * 60)
print("ALL FILINGS PROCESSED")
print(f"Results saved to: {output_file}")
print("=" * 60)
