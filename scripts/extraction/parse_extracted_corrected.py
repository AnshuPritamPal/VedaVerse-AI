"""
Bhagavad Gita As It Is: extracted text -> structured JSON

Is file ki text ka structure (har verse ke liye):

    TEXT 3
    <garbled Sanskrit (purane PDF font ka)>  )) 3 ))      <- verse yahan khatam
    <IAST transliteration, 4 lines>
    <word-for-word: word—meaning; word—meaning; ...>
    TRANSLATION
    ...
    PURPORT
    ...

Ismein "TRANSLITERATION" ya "WORD FOR WORD" naam ke headings hote hi nahi,
isliye in dono ko alag karne ke liye verse-end marker "))  N  ))" aur
em-dash "—" ka use kiya gaya hai.

Run (project root se):
    python scripts/extraction/parse_extracted_corrected.py
    python scripts/extraction/parse_extracted_corrected.py data/full_extraction.txt data/parsed_full_v2.json

Devanagari ke liye (ek baar):
    pip install indic-transliteration
"""

import json
import re
import sys
from pathlib import Path

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

INPUT_FILE = Path("data/full_extraction.txt")
OUTPUT_FILE = Path("data/parsed_full_v2.json")

SOURCE_NAME = "Bhagavad Gita As It Is"
AUTHOR = "A.C. Bhaktivedanta Swami Prabhupada"
CHAPTER_NAMES = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
    "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
    "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14,
    "FIFTEEN": 15, "SIXTEEN": 16, "SEVENTEEN": 17, "EIGHTEEN": 18,
}

# PDF ke Balaram font ke characters (kåñëa, çré, uväca...) ko
# proper Unicode (kṛṣṇa, śrī, uvāca...) mein badalna
FIX_DIACRITICS = True

# Purane font wala garbled "sanskrit" hata kar, transliteration se
# asli Devanagari banana (indic-transliteration library chahiye)
MAKE_DEVANAGARI = True


# --------------------------------------------------
# PATTERNS
# --------------------------------------------------

# "TEXT 3" ya "TEXTS 42-43" (akeli line mein)
VERSE_HEADING = re.compile(
    r"^[ \t]*TEXTS?[ \t]+(\d+)(?:[ \t]*[-–—][ \t]*(\d+))?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


CHAPTER_HEADING = re.compile(
    r"^[ \t]*CHAPTER[ \t]+"
    r"(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|"
    r"ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|"
    r"SEVENTEEN|EIGHTEEN)\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)

TRANSLATION_HEADING = re.compile(
    r"^[ \t]*TRANSLATION\b[ \t]*:?[ \t]*", re.IGNORECASE | re.MULTILINE
)
PURPORT_HEADING = re.compile(
    r"^[ \t]*PURPORT\b[ \t]*:?[ \t]*", re.IGNORECASE | re.MULTILINE
)

# "======= PDF PAGE 87 =======" (aas-paas ki khali lines ke saath)
PAGE_MARKER = re.compile(
    r"\s*={5,}[ \t]*PDF[ \t]+PAGE[ \t]+\d+[ \t]*={5,}[ \t]*(?:\n|$)"
)

# garbled Sanskrit ke end ka marker: ")) 3 ))"  ya  ")) 42-43 ))"
VERSE_END_MARK = re.compile(r"\)\)[ \t]*\d+(?:[ \t]*[-–—][ \t]*\d+)?[ \t]*\)\)")

# Input is UTF-8 and already contains proper IAST. Do not remap characters.
# TEXT HELPERS
# --------------------------------------------------

def clean_text(text):
    """Extra whitespace hatao, paragraphs rakho."""
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    return text.strip()


def remove_page_markers(text):
    """Page marker hatao. Beech ke sentence ko jodne ke liye ek newline chhodo."""
    return PAGE_MARKER.sub("\n", text)


def fix_diacritics(text):
    return text


def join_lines(lines):
    """
    Hard-wrapped lines ko ek line mein jodo.
    'äkula—' + 'depressed'  -> 'äkula—depressed'   (dash ke baad space nahi)
    'svabhävaù' + '—characteristics' -> 'svabhävaù—characteristics'
    'so-' + 'called' -> 'so-called'
    """
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not out:
            out = line
        elif out.endswith(("-", "—")) or line.startswith("—"):
            out += line
        else:
            out += " " + line
    return out


def join_paragraphs(text):
    """
    Purport ke liye: hard-wrapped lines jodo, par paragraphs alag rakho.
    Nayi paragraph = blank line ke baad ya space se shuru hone wali line.
    """
    paragraphs = []
    current = []
    for line in text.splitlines():
        if not line.strip():
            if current:
                paragraphs.append(join_lines(current))
                current = []
            continue
        if line.startswith(" ") and current:
            paragraphs.append(join_lines(current))
            current = []
        current.append(line)
    if current:
        paragraphs.append(join_lines(current))
    return "\n\n".join(p for p in paragraphs if p)


# --------------------------------------------------
# DEVANAGARI
# --------------------------------------------------

_devanagari_ready = None


def to_devanagari(iast_text):
    """IAST transliteration -> Devanagari. Library na ho to '' wapas."""
    global _devanagari_ready
    try:
        from indic_transliteration import sanscript
    except ImportError:
        if _devanagari_ready is None:
            print(
                "NOTE: Devanagari nahi ban paya. Install karo: "
                "pip install indic-transliteration"
            )
        _devanagari_ready = False
        return ""

    _devanagari_ready = True
    lines = []
    for line in iast_text.splitlines():
        line = line.replace("’", "'").replace("ṁ", "ṃ").replace("Ṁ", "Ṃ")
        line = line.replace("-", "")  # compound ke hyphens
        lines.append(
            sanscript.transliterate(line, sanscript.IAST, sanscript.DEVANAGARI)
        )
    return "\n".join(lines)


# --------------------------------------------------
# WORD-FOR-WORD  ->  [{"word": ..., "meaning": ...}]
# --------------------------------------------------

def parse_word_meanings(word_for_word):
    if not word_for_word:
        return []

    text = word_for_word.strip().rstrip(".")

    # kabhi kabhi ';' ki jagah ',' likha hota hai:
    # "ca—also, madhusüdana—O killer"  ->  ek comma ke baad "word—" aaye to split
    text = re.sub(r",\s+(?=[^\s;,—]+—)", "; ", text)

    pairs = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "—" in chunk:
            word, meaning = chunk.split("—", 1)
            pairs.append({"word": word.strip(), "meaning": meaning.strip()})
        elif pairs:
            # meaning ke andar ';' tha
            pairs[-1]["meaning"] += "; " + chunk
        else:
            pairs.append({"word": "", "meaning": chunk})
    return pairs


# --------------------------------------------------
# PARSE ONE VERSE
# --------------------------------------------------

def split_verse_head(head):
    """
    TEXT heading aur TRANSLATION ke beech ka hissa ->
    (garbled sanskrit, transliteration lines, word-for-word lines)
    """
    mark = VERSE_END_MARK.search(head)
    if mark:
        garbled = head[:mark.end()]
        rest = head[mark.end():]
    else:
        # marker nahi mila: pehla paragraph garbled maan lo
        parts = re.split(r"\n\s*\n", head.strip(), maxsplit=1)
        garbled = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

    lines = [ln.strip() for ln in rest.strip().splitlines() if ln.strip()]

    # word-for-word wahan se shuru jahan pehli baar "—" aata hai
    start = next((i for i, ln in enumerate(lines) if "—" in ln), None)
    if start is None:
        return garbled, lines, []
    return garbled, lines[:start], lines[start:]


def parse_verse(block, chapter, verse_number, verse_label):
    block = remove_page_markers(block)

    # ---- headings ke hisaab se 3 hisse: head | translation | purport
    translation_match = TRANSLATION_HEADING.search(block)
    if translation_match:
        head = block[:translation_match.start()]
        after = block[translation_match.end():]
    else:
        head, after = block, ""

    purport_match = PURPORT_HEADING.search(after)
    if purport_match:
        translation_raw = after[:purport_match.start()]
        purport_raw = after[purport_match.end():]
    else:
        # purport na ho to bhi translation poori milni chahiye
        translation_raw, purport_raw = after, ""

    # ---- head: sanskrit | transliteration | word-for-word
    _garbled, iast_lines, wfw_lines = split_verse_head(head)

    transliteration = fix_diacritics("\n".join(iast_lines))
    word_for_word = fix_diacritics(join_lines(wfw_lines))

    sanskrit = to_devanagari(transliteration) if MAKE_DEVANAGARI else ""

    translation = fix_diacritics(join_lines(translation_raw.splitlines()))
    purport = fix_diacritics(join_paragraphs(purport_raw))

    return {
        "source": SOURCE_NAME,
        "chapter": chapter,
        "verse": verse_number,
        "verse_label": verse_label,
        "sanskrit": sanskrit,
        "transliteration": transliteration,
        "word_for_word": word_for_word,
        "word_meanings": parse_word_meanings(word_for_word),
        "translation": {
            "text": translation,
            "author": AUTHOR,
        },
        "purport": {
            "text": purport,
            "author": AUTHOR,
        },
    }


# --------------------------------------------------
# MAIN PARSER
# --------------------------------------------------

def parse_file(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        return

    raw_text = clean_text(input_file.read_text(encoding="utf-8"))

    matches = list(VERSE_HEADING.finditer(raw_text))
    chapter_matches = list(CHAPTER_HEADING.finditer(raw_text))
    records = []

    for index, match in enumerate(matches):
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) else None
        label = f"{first}-{last}" if last else str(first)

        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(raw_text)
        )

        chapter = None
        for chapter_match in chapter_matches:
            if chapter_match.start() > match.start():
                break
            chapter = CHAPTER_NAMES[chapter_match.group(1).upper()]

        if chapter is None:
            raise ValueError(f"Chapter heading not found before verse {label}")

        records.append(
            parse_verse(raw_text[start:end], chapter, first, label)
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    # ---------------- summary ----------------
    total = len(records)
    print(f"Total verse headings found: {len(matches)}")
    print(f"Records saved: {total}")
    print(f"Chapters detected: {sorted(set(r['chapter'] for r in records))}")
    print(f"Output: {output_file}")

    print("\nField extraction status:")
    for field in ["sanskrit", "transliteration", "word_for_word", "word_meanings"]:
        count = sum(1 for r in records if r[field])
        print(f"{field}: {count}/{total}")
    for field in ["translation", "purport"]:
        count = sum(1 for r in records if r[field]["text"])
        print(f"{field}: {count}/{total}")

    # purport kai verses mein hota hi nahi, isliye usse "missing" nahi ginte
    required = ["transliteration", "word_for_word", "translation"]

    def is_missing(record, name):
        value = record[name]
        return not (value["text"] if isinstance(value, dict) else value)

    incomplete = [
        f"Chapter {r['chapter']}, Verse {r['verse_label']}: "
        + ", ".join(n for n in required if is_missing(r, n))
        for r in records
        if any(is_missing(r, n) for n in required)
    ]

    print("\nVerses with missing fields:")
    if incomplete:
        for line in incomplete:
            print("-", line)
    else:
        print("None")

    no_purport = [r["verse_label"] for r in records if not r["purport"]["text"]]
    if no_purport:
        print("\nVerses without purport (normal for many verses):")
        print("-", ", ".join(no_purport))

    # ---------------- sanity warnings ----------------
    # 1) purport beech sentence mein khatam ho -> aksar extraction file
    #    ya page range wahin kat gayi hoti hai
    sentence_end = (".", "?", "!", "”", '"', "’", ")", ":")
    maybe_cut = [
        r["verse_label"]
        for r in records
        if r["purport"]["text"]
        and not r["purport"]["text"].rstrip().endswith(sentence_end)
    ]
    print("\nPurports that may be cut off (check next page / page range):")
    print("-", ", ".join(maybe_cut) if maybe_cut else "None")

    # 2) word-meaning pairs jo galat split hue ho sakte hain
    odd_pairs = []
    for r in records:
        for p in r["word_meanings"]:
            if not p["word"] or not p["meaning"] or len(p["word"].split()) > 3:
                odd_pairs.append(
                    f"Verse {r['verse_label']}: {p['word']!r} -> {p['meaning']!r}"
                )
    print("\nWord-meaning pairs to double-check:")
    if odd_pairs:
        for line in odd_pairs:
            print("-", line)
    else:
        print("None")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console ke liye
    except Exception:
        pass

    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_FILE
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_FILE
    parse_file(in_path, out_path)
