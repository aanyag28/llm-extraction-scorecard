from pathlib import Path
from bs4 import BeautifulSoup


def extract_text(file_path):
    html = Path(file_path).read_text(
        encoding="utf-8",
        errors="ignore"
    )

    soup = BeautifulSoup(html, "html.parser")

    # Remove metadata and code sections
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


def process_filing(file_path):
    text = extract_text(file_path)

    output_file = Path(file_path).with_suffix(".txt")
    output_file.write_text(text, encoding="utf-8")

    print(f"Processed: {file_path}")
    print(f"Saved: {output_file}")
    print(f"Characters: {len(text)}")


process_filing("PR_10K_2025.html")