import pymupdf

pdf_path = "Bhagavad-gita-As-It-Is.pdf"

doc = pymupdf.open(pdf_path)
page = doc[12]

print("FONT INFORMATION:")
for font in page.get_fonts(full=True):
    print(font)

print("\nRAW TEXT DICTIONARY:")
data = page.get_text("dict")

for block in data["blocks"]:
    if "lines" not in block:
        continue

    for line in block["lines"]:
        for span in line["spans"]:
            print({
                "font": span["font"],
                "text": span["text"][:150],
                "chars": span.get("chars", [])[:10]
            })

doc.close()