from pathlib import Path

FILE_PATH = Path("data/full_extraction_corrected.txt")

def main():
    if not FILE_PATH.exists():
        print("Corrected text file not found!")
        return

    text = FILE_PATH.read_text(encoding="utf-8")

    suspicious_chars = ["Â", "¤"]

    print("INSPECTING REMAINING SUSPICIOUS CHARACTERS")
    print("=" * 50)

    for char in suspicious_chars:
        print(f"\nCharacter: {repr(char)}")
        print("-" * 50)

        count = 0

        for line_number, line in enumerate(
            text.splitlines(), start=1
        ):
            if char in line:
                print(f"Line {line_number}: {line.strip()}")
                count += 1

        print(f"Total lines containing {repr(char)}: {count}")

if __name__ == "__main__":
    main()