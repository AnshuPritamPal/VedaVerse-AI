
import argparse
import re
from pathlib import Path

import pymupdf  # PyMuPDF



def extract_pages(pdf_path, start_page, end_page):
    doc = pymupdf.open(pdf_path)

    if start_page < 1 or end_page > len(doc) or start_page > end_page:
        raise ValueError(
            f"Choose a valid page range between 1 and {len(doc)}"
        )

    extracted = []

    for page_number in range(start_page, end_page + 1):
        page = doc[page_number - 1]
        text = page.get_text("text", sort=True).strip()
        extracted.append((page_number, text))

    doc.close()
    return extracted


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDF text for VedaVerse AI"
    )

    parser.add_argument("--pdf", required=True)
    parser.add_argument("--start", type=int, default=82)
    parser.add_argument("--end", type=int, default=90)
    parser.add_argument(
        "--output",
        default="data/extraction_test.txt"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = extract_pages(pdf_path, args.start, args.end)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for page_number, text in pages:
            file.write(
                f"\n{'=' * 24} PDF PAGE {page_number} "
                f"{'=' * 24}\n"
            )
            file.write(text or "[NO SELECTABLE TEXT FOUND]")
            file.write("\n")

    nonempty = sum(bool(text) for _, text in pages)

    print(f"Pages processed: {len(pages)}")
    print(f"Pages with selectable text: {nonempty}")
    print(f"Output saved to: {output_path.resolve()}")

    print("\nPreview:")

    for page_number, text in pages[:2]:
        preview = re.sub(r"\s+", " ", text)[:500]
        print(f"\nPage {page_number}: {preview or '[no text]'}")


if __name__ == "__main__":
    main()