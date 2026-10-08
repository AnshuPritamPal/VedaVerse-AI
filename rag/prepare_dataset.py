
import json
import re
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "parsed_full_v2.json"
OUTPUT_PATH = BASE_DIR / "data" / "clean_dataset.json"
VERSE_OUTPUT_PATH = BASE_DIR / "data" / "verse_dataset.json"


# --------------------------------------------------
# TARGETED SPELLING CORRECTIONS
# Used for English translation and purport only.
# --------------------------------------------------

WORD_CORRECTIONS = {
    # Names and important terms
    "Dhåtaräñöra": "Dhṛtarāṣṭra",
    "dhåtaräñöra": "dhṛtarāṣṭra",
    "Saïjaya": "Sañjaya",
    "saïjaya": "sañjaya",
    "Kurukñetra": "Kurukṣetra",
    "kurukñetra": "kurukṣetra",
    "Bhagavad-gétä": "Bhagavad-gītā",
    "bhagavad-gétä": "bhagavad-gītā",
    "Gétä-mähätmya": "Gītā-māhātmya",
    "Gétä": "Gītā",
    "gétä": "gītā",
    "Çré Kåñëa": "Śrī Kṛṣṇa",
    "Çré": "Śrī",
    "çré": "śrī",
    "Kåñëa": "Kṛṣṇa",
    "kåñëa": "kṛṣṇa",
    "Viñëu": "Viṣṇu",
    "viñëu": "viṣṇu",
    "Räma": "Rāma",
    "Bhägavatam": "Bhāgavatam",
    "Çrémad": "Śrīmad",
    "Brahmä": "Brahmā",
    "Paramätmä": "Paramātmā",
    "yogé": "yogī",
    "Vedänta": "Vedānta",
    "saàhitä": "saṃhitā",
    "yajïa": "yajña",
    "brähmaëa": "brāhmaṇa",
    "kñatriya": "kṣatriya",
    "mäyä": "māyā",
    "jïäna": "jñāna",
    "Näräyaëa": "Nārāyaṇa",
    "Upaniñad": "Upaniṣad",
    "säìkhya": "sāṅkhya",
    "sannyäsé": "sannyāsī",
    "Våndävana": "Vṛndāvana",
    "Bhéñma": "Bhīṣma",
    "Kunté": "Kuntī",
    "kñatriyas": "kṣatriyas",
    "Påthä": "Pṛthā",
    "Bhagavän": "Bhagavān",
    "Mäyävädé": "Māyāvādī",
    "Vyäsa": "Vyāsa",
    "varëäçrama": "varṇāśrama",
    "Gosvämé": "Gosvāmī",
    "Närada": "Nārada",
    "ätmä": "ātmā",
    "Håñékeça": "Hṛṣīkeśa",
    "samädhi": "samādhi",
    "Mahäräja": "Mahārāja",
    "Päëòavas": "Pāṇḍavas",
    "päëòavas": "pāṇḍavas",
    "Päëòu": "Pāṇḍu",
    "Päëòus": "Pāṇḍus",
    "Pāṇòu": "Pāṇḍu",
    "Väsudeva": "Vāsudeva",
    "mahätmä": "mahātmā",
    "Devaké": "Devakī",
    "sannyäsa": "sannyāsa",
    "Vyäsadeva": "Vyāsadeva",
    "änanda": "ānanda",
    "Droëäcärya": "Droṇācārya",
    "droëäcärya": "droṇācārya",
    "Kaöha": "Kaṭha",
    "paraà": "paraṃ",
    "Puräëa": "Purāṇa",
    "småti": "smṛti",
    "Çréla": "Śrīla",
    "Vivasvän": "Vivasvān",
    "brahmacäré": "brahmacārī",
    "dharma-kñetra": "dharma-kṣetra",
    "dharma-kñetre": "dharma-kṣetre",
    "kuru-kñetre": "kuru-kṣetre",
    "Yudhiñöhira": "Yudhiṣṭhira",

    # Chapter 1 names
    "Draupadé": "Draupadī",
    "Bhéma": "Bhīma",
    "Yuyudhäna": "Yuyudhāna",
    "Viräöa": "Virāṭa",
    "Dhåñöadyumna": "Dhṛṣṭadyumna",
    "Dhåñöaketu": "Dhṛṣṭaketu",
    "Cekitäna": "Cekitāna",
    "Käçiräja": "Kāśirāja",
    "Çaibya": "Śaibya",
    "Karëa": "Karṇa",
    "Kåpa": "Kṛpa",
    "Açvatthämä": "Aśvatthāmā",
    "Vikarëa": "Vikarṇa",
    "Bhuriçravä": "Bhūriśravā",
    "Bhüriçravä": "Bhūriśravā",
    "Bählékas": "Bāhlīkas",
    "Kåtavarmä": "Kṛtavarmā",
    "Çalya": "Śalya",
    "Subhadrä": "Subhadrā",
    "Yudhämanyu": "Yudhāmanyu",
    "Uttamaujä": "Uttamaujas",
    "Kåpäcärya": "Kṛpācārya",

    # Additional terms
    "Droëa": "Droṇa",
    "Vaiñëava": "Vaiṣṇava",
    "Çvetäçvatara": "Śvetāśvatara",
    "prakåti": "prakṛti",
    "Vaikuëöha": "Vaikuṇṭha",
    "näma": "nāma",
    "añöäìga": "aṣṭāṅga",
    "saìkértana": "saṅkīrtana",
    "Pärtha": "Pārtha",
    "jéva": "jīva",
    "avatära": "avatāra",
    "rasämåta": "rasāmṛta",
    "çüdras": "śūdras",
    "Pataïjali": "Patañjali",
    "haöha": "haṭha",
    "Kaàsa": "Kaṃsa",
    "dhyäna": "dhyāna",
    "puruña": "puruṣa",
    "Çyämasundara": "Śyāmasundara",
    "Rüpa": "Rūpa",
    "prasädam": "prasādam",
    "sütra": "sūtra",
    "sütras": "sūtras",
    "ahaà": "ahaṃ",
    "paramaà": "paramaṃ",
    "puruñaà": "puruṣaṃ",
    "manaù": "manaḥ",

    # Citation abbreviation
    "Bhäg.": "Bhāg.",
}


# --------------------------------------------------
# TEXT CLEANING
# --------------------------------------------------

def clean_text(text, apply_corrections=False):
    """Normalize text and optionally apply known corrections."""

    if not isinstance(text, str):
        return ""

    # Remove soft hyphens
    text = text.replace("\u00ad", "")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Apply corrections only where intended
    if apply_corrections:
        for wrong, correct in WORD_CORRECTIONS.items():
            text = text.replace(wrong, correct)

    return text.strip()


# --------------------------------------------------
# TEXT CHUNKING
# --------------------------------------------------

def split_into_chunks(text, max_words=220, overlap=40):
    """Split long purports into overlapping word-based chunks."""

    words = text.split()

    if not words:
        return []

    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - overlap

    return chunks


# --------------------------------------------------
# EXTRACT TEXT FROM ORIGINAL FIELDS
# --------------------------------------------------

def get_text(value):
    """Support strings and nested {'text': ...} fields."""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return value.get("text", "")

    return ""


# --------------------------------------------------
# CLEAN STRUCTURED WORD MEANINGS
# --------------------------------------------------

def clean_word_meanings(value):
    """Preserve word meanings as a list of word/meaning objects."""

    if not isinstance(value, list):
        return []

    cleaned = []

    for item in value:
        if not isinstance(item, dict):
            continue

        word = clean_text(item.get("word", ""))
        meaning = clean_text(
            item.get("meaning", ""),
            apply_corrections=True
        )

        if word or meaning:
            cleaned.append({
                "word": word,
                "meaning": meaning
            })

    return cleaned


# --------------------------------------------------
# MAIN DATASET PREPARATION
# --------------------------------------------------

def main():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_PATH}")

    # Load original parsed dataset
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        records = json.load(file)

    clean_records = []
    verse_records = []

    for record in records:

        chapter = record.get("chapter")
        verse = record.get(
            "verse_label",
            record.get("verse", "")
        )

        reference = f"Bhagavad Gita {chapter}.{verse}"

        # ------------------------------------------
        # VERSE-LEVEL FIELDS
        # ------------------------------------------

        # Preserve Sanskrit and transliteration as extracted.
        # These may need a separate verification/correction pass.
        sanskrit = clean_text(record.get("sanskrit", ""))
        transliteration = clean_text(
            record.get("transliteration", "")
        )

        word_for_word = clean_text(
            record.get("word_for_word", ""),
            apply_corrections=True
        )

        word_meanings = clean_word_meanings(
            record.get("word_meanings", [])
        )

        translation = clean_text(
            get_text(record.get("translation")),
            apply_corrections=True
        )

        purport = clean_text(
            get_text(record.get("purport")),
            apply_corrections=True
        )

        # Skip only if the record has no usable content at all
        if not any([
            sanskrit,
            transliteration,
            word_for_word,
            word_meanings,
            translation,
            purport
        ]):
            continue

        source = record.get(
            "source",
            "Bhagavad Gita As It Is"
        )

        # Store one complete record per verse
        verse_records.append({
            "source": source,
            "chapter": chapter,
            "verse": verse,
            "reference": reference,
            "sanskrit": sanskrit,
            "transliteration": transliteration,
            "word_for_word": word_for_word,
            "word_meanings": word_meanings,
            "translation": translation,
            "purport": purport
        })

        # ------------------------------------------
        # STORE TRANSLATION DOCUMENT
        # ------------------------------------------

        if translation:
            clean_records.append({
                "source": source,
                "chapter": chapter,
                "verse": verse,
                "reference": reference,
                "content_type": "translation",
                "text": (
                    f"{reference}\n"
                    f"Translation:\n{translation}"
                ),
                "sanskrit": sanskrit,
                "transliteration": transliteration,
                "word_for_word": word_for_word,
                "word_meanings": word_meanings,
                "translation": translation,
                "purport": ""
            })

        # ------------------------------------------
        # SPLIT AND STORE PURPORT DOCUMENTS
        # ------------------------------------------

        if purport:
            chunks = split_into_chunks(purport)

            for i, chunk in enumerate(chunks, start=1):
                clean_records.append({
                    "source": source,
                    "chapter": chapter,
                    "verse": verse,
                    "reference": reference,
                    "content_type": "purport",
                    "chunk": i,
                    "text": (
                        f"{reference}\n"
                        f"Purport:\n{chunk}"
                    ),
                    "sanskrit": sanskrit,
                    "transliteration": transliteration,
                    "word_for_word": word_for_word,
                    "word_meanings": word_meanings,
                    "translation": translation,
                    "purport": chunk
                })

    # ------------------------------------------
    # SAVE OUTPUT FILES
    # ------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(VERSE_OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            verse_records,
            file,
            ensure_ascii=False,
            indent=2
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            clean_records,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ------------------------------------------
    # SUMMARY
    # ------------------------------------------

    print("Dataset preparation completed!")
    print(f"Original records: {len(records)}")
    print(f"Complete verse records: {len(verse_records)}")
    print(f"Searchable documents: {len(clean_records)}")
    print(f"Verse output: {VERSE_OUTPUT_PATH}")
    print(f"Search output: {OUTPUT_PATH}")


# --------------------------------------------------
# RUN SCRIPT
# --------------------------------------------------

if __name__ == "__main__":
    main()