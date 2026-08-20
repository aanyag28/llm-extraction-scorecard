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

Find the company's total revenue for the fiscal year ended
December 31, 2025.

Return ONLY:

Revenue: [amount]
Currency: [currency]
Fiscal year: [year]

Do not explain your answer.

SEC filing:
{text}
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)

print(response.text)
