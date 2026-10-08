import re
from pathlib import Path
from collections import Counter

# --------------------------------------------------
# 1. File paths
# --------------------------------------------------

INPUT_FILE = Path("data/full_extraction.txt")
OUTPUT_FILE = Path("data/full_extraction_corrected.txt")
REPORT_FILE = Path("data/correction_report.txt")


# --------------------------------------------------
# 2. Character correction mapping
# --------------------------------------------------
# These mappings are based on the extraction errors
# identified in our current Bhagavad Gita text.
#
# Example:
# Kåñëa -> Kṛṣṇa
# Bhagavad-gétä -> Bhagavad-gītā

CHARACTER_MAP = {
    "ç": "ś",
    "Ç": "Ś",
    "å": "ṛ",
    "ë": "ṇ",
    "ï": "ñ",
    "ñ": "ṣ",
    "ä": "ā",
    "é": "ī",
    "ü": "ū",
    "ù": "ḥ",
    "à": "ṃ",
}


# --------------------------------------------------
# 3. Correct the text and count replacements
# --------------------------------------------------

def correct_text(text):
    corrected_chars = []
    replacement_counts = Counter()

    for char in text:
        if char in CHARACTER_MAP:
            corrected_chars.append(CHARACTER_MAP[char])
            replacement_counts[char] += 1
        else:
            corrected_chars.append(char)

    return "".join(corrected_chars), replacement_counts


# --------------------------------------------------
# 4. Find suspicious characters
# --------------------------------------------------

def find_suspicious_characters(text):
    # These are indicators for manual inspection,
    # not proof that a character is incorrect.
    suspicious = ["Ã", "Â", "�", "¤", "�"]

    findings = {}

    for char in suspicious:
        count = text.count(char)
        if count > 0:
            findings[char] = count

    return findings


# --------------------------------------------------
# 5. Main function
# --------------------------------------------------

def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    print("Reading original extracted text...")

    original_text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    print("Correcting known character-mapping errors...")

    corrected_text, replacement_counts = correct_text(
        original_text
    )

    print("Checking for suspicious characters...")

    suspicious = find_suspicious_characters(
        corrected_text
    )

    # Save corrected text separately
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        corrected_text,
        encoding="utf-8"
    )

    # Generate correction report
    report = []

    report.append("BHAGAVAD GITA TEXT CORRECTION REPORT")
    report.append("=" * 45)
    report.append(f"Input file: {INPUT_FILE}")
    report.append(f"Output file: {OUTPUT_FILE}")
    report.append(f"Original characters: {len(original_text)}")
    report.append(f"Corrected characters: {len(corrected_text)}")
    report.append("")

    report.append("CHARACTER REPLACEMENTS")
    report.append("-" * 45)

    total_replacements = 0

    for old_char, count in sorted(
        replacement_counts.items()
    ):
        new_char = CHARACTER_MAP[old_char]
        report.append(
            f"{old_char} -> {new_char}: {count}"
        )
        total_replacements += count

    report.append("")
    report.append(
        f"Total replacements: {total_replacements}"
    )

    report.append("")
    report.append("SUSPICIOUS CHARACTERS")
    report.append("-" * 45)

    if suspicious:
        for char, count in suspicious.items():
            report.append(
                f"{repr(char)}: {count} occurrences"
            )
    else:
        report.append(
            "No configured suspicious characters found."
        )

    report.append("")
    report.append(
        "NOTE: This report does not verify Sanskrit accuracy."
    )
    report.append(
        "Manually compare selected verses with a trusted source."
    )

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\nCorrection completed!")
    print(f"Corrected text: {OUTPUT_FILE}")
    print(f"Report: {REPORT_FILE}")
    print(f"Total replacements: {total_replacements}")

    if suspicious:
        print("\nWarning: Suspicious characters remain.")
        for char, count in suspicious.items():
            print(f"{repr(char)}: {count} occurrences")


if __name__ == "__main__":
    main()