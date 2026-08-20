from pathlib import Path
import os
from google import genai

# Connect to Gemini
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# Read the cleaned SEC filing
text = Path("PR_10K_2025.txt").read_text(
    encoding="utf-8",
    errors="ignore"
)

# Ask Gemini to extract revenue
prompt = f"""
You are extracting financial information from an SEC 10-K filing.

Find these three financial metrics for the fiscal year ended
December 31, 2025:

1. Total revenue
2. Average daily production volume
3. Capital expenditures

For each metric, return:
- Metric name
- Exact amount
- Unit
- Fiscal year
- Section or table where you found it

Use the value reported in the filing. Do not calculate or estimate
a value unless the filing explicitly requires it.

SEC filing:
{text}
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)

print(f"File: PR_10K_2025.txt")
print(response.text)
