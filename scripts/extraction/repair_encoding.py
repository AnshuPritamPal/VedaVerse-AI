
from pathlib import Path

input_path = Path("data/full_extraction.txt")
output_path = Path("data/full_extraction_repaired.txt")

text = input_path.read_text(encoding="utf-8")

def repair_line(line):
    try:
        return line.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return line

repaired_lines = [
    repair_line(line)
    for line in text.splitlines(keepends=True)
]

repaired = "".join(repaired_lines)
output_path.write_text(repaired, encoding="utf-8")

print("Repaired file saved to:", output_path.resolve())
print("\nPreview:")
print(repaired[:1500])