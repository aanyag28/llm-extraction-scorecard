from pathlib import Path
from bs4 import BeautifulSoup
import os
from google import genai


def extract_text(file_path):
    html = Path(file_path).read_text(
        encoding="utf-8",
        errors="ignore"
    )

    soup = BeautifulSoup(html, "html.parser")

    # Remove metadata and code
    for tag in soup.find_all([
        "script",
        "style",
        "ix:header",
        "ix:hidden",
        "head"
    ]):
        tag.decompose()

    # Remove XBRL elements
    for tag in soup.find_all():
        if tag.name and (
            tag.name.startswith("ix:")
            or tag.name.startswith("xbrli:")
        ):
            tag.decompose()

    return soup.get_text(" ", strip=True)


# Connect to Gemini
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# Read the SEC filing
text = extract_text("PR_10K_2025.html")

# Ask Gemini to find revenue
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
