import pymupdf
from pathlib import Path
import re

# ==================================================
# 1. CONFIGURATION
# ==================================================

# Run this script from the project root folder.
PDF_PATH = Path("Bhagavad-gita-As-It-Is.pdf")

OUTPUT_DIR = Path("data/extraction_tests")
OUTPUT_FILE = OUTPUT_DIR / "extraction_results.txt"

# These are the verse headings we want to investigate.
TARGETS = {
    "BG 2.3": ["TEXT 3"],
    "BG 2.7": ["TEXT 7"],
    "BG 2.8": ["TEXT 8"],
}

# Search around the known approximate PDF pages first.
# These are zero-based PDF page indices.
# If a heading is not found, the script searches all pages.
APPROXIMATE_PAGES = {
    "BG 2.3": 0,
    "BG 2.7": 0,
    "BG 2.8": 0,
}


# ==================================================
# 2. HELPER FUNCTIONS
# ==================================================

def normalize_text(text):
    """Normalize whitespace for easier text searching."""
    return re.sub(r"\s+", " ", text).strip()


def search_target(doc, target_name, headings):
    """
    Search the PDF for a target heading.

    First tries normal text extraction.
    Returns the page index if found.
    """

    for page_index, page in enumerate(doc):
        text = page.get_text("text")
        normalized = normalize_text(text).lower()

        for heading in headings:
            if heading.lower() in normalized:
                return page_index

    return None


def extract_standard(page):
    """Extract text using the standard text mode."""
    return page.get_text("text")


def extract_blocks(page):
    """Extract text grouped into blocks."""
    blocks = page.get_text("blocks")

    output = []

    for block in blocks:
        if len(block) > 4:
            content = block[4].strip()

            if content:
                output.append(content)

    return "\n\n".join(output)


def extract_words(page):
    """Extract individual words with their positions."""
    words = page.get_text("words")

    output = []

    for word in words:
        x0, y0, x1, y1, text = word[:5]

        output.append(
            f"Text: {text!r} | "
            f"Position: ({x0:.1f}, {y0:.1f}, "
            f"{x1:.1f}, {y1:.1f})"
        )

    return "\n".join(output)


def extract_raw_details(page):
    """Inspect fonts and character-level extraction."""
    data = page.get_text("rawdict")

    output = []

    for block_index, block in enumerate(data.get("blocks", [])):
        if "lines" not in block:
            continue

        for line_index, line in enumerate(block["lines"]):
            for span_index, span in enumerate(line["spans"]):
                chars = span.get("chars", [])

                extracted = "".join(
                    char.get("c", "")
                    for char in chars
                )

                if not extracted.strip():
                    continue

                output.append(
                    f"Block {block_index}, "
                    f"Line {line_index}, "
                    f"Span {span_index}\n"
                    f"Font: {span.get('font')}\n"
                    f"Size: {span.get('size')}\n"
                    f"Text: {extracted!r}\n"
                )

    return "\n".join(output)


# ==================================================
# 3. PROCESS EACH TARGET
# ==================================================

def inspect_target(doc, target_name, headings):
    """Run all extraction tests for one target."""

    print(f"\nSearching for {target_name}...")

    page_index = search_target(doc, target_name, headings)

    if page_index is None:
        return (
            f"\n{'=' * 70}\n"
            f"{target_name}: HEADING NOT FOUND\n"
            f"{'=' * 70}\n"
            "The heading may itself be affected by font encoding.\n"
        )

    page = doc[page_index]

    print(
        f"Found {target_name} on PDF page "
        f"{page_index + 1}"
    )

    result = []

    result.append("\n" + "=" * 70)
    result.append(f"TARGET: {target_name}")
    result.append(f"PDF PAGE: {page_index + 1}")
    result.append("=" * 70)

    # Standard extraction
    result.append("\n\n--- STANDARD TEXT EXTRACTION ---\n")
    result.append(extract_standard(page))

    # Block extraction
    result.append("\n\n--- BLOCK EXTRACTION ---\n")
    result.append(extract_blocks(page))

    # Word extraction
    result.append("\n\n--- WORD EXTRACTION ---\n")
    result.append(extract_words(page))

    # Raw character and font inspection
    result.append("\n\n--- RAW CHARACTER AND FONT DETAILS ---\n")
    result.append(extract_raw_details(page))

    # Save a page image for visual comparison
    image_path = OUTPUT_DIR / (
        f"{target_name.replace(' ', '_')}_page.png"
    )

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(2, 2),
        alpha=False
    )

    pix.save(image_path)

    result.append(
        f"\n\nPage image saved to: {image_path}"
    )

    return "\n".join(result)


# ==================================================
# 4. MAIN
# ==================================================

def main():
    if not PDF_PATH.exists():
        print("ERROR: PDF not found!")
        print(f"Expected location: {PDF_PATH.resolve()}")
        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Opening Bhagavad Gita PDF...")
    print(f"File: {PDF_PATH.resolve()}")

    doc = pymupdf.open(PDF_PATH)

    print(f"Total PDF pages: {len(doc)}")

    all_results = []

    for target_name, headings in TARGETS.items():
        result = inspect_target(
            doc,
            target_name,
            headings
        )

        all_results.append(result)

    doc.close()

    final_output = "\n\n".join(all_results)

    OUTPUT_FILE.write_text(
        final_output,
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("EXTRACTION TEST COMPLETED")
    print("=" * 60)
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Full path: {OUTPUT_FILE.resolve()}")

    print("\nOpen the result file and inspect the extracted text.")
    print("Compare it with the generated page images.")


if __name__ == "__main__":
    main()
