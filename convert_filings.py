from pathlib import Path
from bs4 import BeautifulSoup

# Find all HTML SEC filings in the project folder
html_files = Path(".").glob("*.html")

for html_file in html_files:

    print(f"Converting: {html_file.name}")

    # Read the HTML
    html = html_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove only things that are definitely not filing text
    for tag in soup.find_all(["script", "style", "head"]):
        tag.decompose()

    # Extract all text
    text = soup.get_text("\n", strip=True)

    # Create TXT filename
    txt_file = html_file.with_suffix(".txt")

    # Save text
    txt_file.write_text(
        text,
        encoding="utf-8"
    )

    print(f"Created: {txt_file.name}")
    print(f"Characters: {len(text):,}")
    print(f"Lines: {len(text.splitlines()):,}")
    print()