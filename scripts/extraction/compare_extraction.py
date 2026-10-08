
from pathlib import Path
import pymupdf

pdf_path = Path("Bhagavad-gita-As-It-Is.pdf")
text_path = Path("data/full_extraction.txt")

doc = pymupdf.open(pdf_path)

# Page 13 in the PDF (zero-based index 12)
page_text = doc[12].get_text("text", sort=True)

saved_text = text_path.read_text(encoding="utf-8")

print("DIRECT PDF EXTRACTION:")
print(page_text[:1200])

print("\nSAVED EXTRACTION:")
marker = "PDF PAGE 13"
position = saved_text.find(marker)

if position == -1:
    print("Page 13 marker not found")
else:
    print(saved_text[position:position + 1500])

doc.close()