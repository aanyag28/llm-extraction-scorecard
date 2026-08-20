from pathlib import Path
import os
from google import genai


# Connect to Gemini
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# Find all SEC filing text files
filings = sorted(Path(".").glob("*.txt"))


# Ignore files that are not SEC filings
filings = [
    file for file in filings
    if file.name not in [
        "answer_key.csv",
        "answer_key.csv-2.txt"
    ]
]


# Process each filing
for file_path in filings:

    print("\n" + "=" * 60)
    print(f"FILE: {file_path.stem.replace('_', ' ')}")
    print("=" * 60)

    # Read the filing
    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    # Ask Gemini to extract the three metrics
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

    # Send the filing to Gemini
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    # Print Gemini's response
    print(response.text)
