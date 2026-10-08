"""
VedaVerse AI - rag.py

Step 1: answer accuracy aur citation validation

Kya badla (purane rag.py ke mukable):
  1. Model ab free-form answer nahi, structured points deta hai. Har scriptural
     point ke saath reference, source (translation/purport) aur ek EXACT quote hota hai.
     Code check karta hai ki quote supplied text mein sach mein hai. Jo point
     verify na ho, wo answer se hata diya jata hai (model ka dawa kaafi nahi).
  2. Practical suggestions alag section mein, "not stated in the scripture" label ke saath.
     (japa/prayer jaisi baatein ab scripture ke naam par nahi aati.)
  3. Har point ke saath source dikhta hai: (Bhagavad Gita 2.63, translation / purport).
  4. Retrieved text kaafi na ho to answer guess nahi karta, saaf bata deta hai.
  5. Claim audit ka overall status ab code se nikalta hai (model ke "supported" par
     bharosa nahi), aur audit ki quote bhi text se match hoti hai.
  6. "Explain 2.47" jaise sawaal par woh verse seedha dataset se aata hai.
     "using only 2.62 and 2.63" par sirf wahi verses use hote hain.
  7. Concise answer default; "in detail" / detailed=True par lamba answer.
  8. Groq 429 par backoff ke saath retry, context size ki limit, aur repeat
     question ke liye cache (model calls kam).
  9. Naya dataset schema (translation/purport {"text": ...}, grouped verses "3-4") supported.
"""

import copy
import json
import logging
import os
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import groq
from dotenv import load_dotenv
from groq import Groq

from .retrieve import retrieve_verses


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

load_dotenv(PROJECT_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Please check your .env file."
    )

# Rate limit (429) hum khud backoff ke saath handle karte hain
client = Groq(api_key=GROQ_API_KEY, max_retries=1)

MODEL_NAME = "openai/gpt-oss-120b"

DISPLAY_NAME = "Bhagavad Gita"

TOP_K = 8

# Model ko jaane wala text: ek verse ki purport aur poore context ki limit
MAX_PURPORT_CHARS = 7000
MAX_CONTEXT_CHARS = 18000

# Concise / detailed mode ki limits
MAX_POINTS_CONCISE = 3
MAX_POINTS_DETAILED = 6
MAX_TIPS_CONCISE = 2
MAX_TIPS_DETAILED = 4

# Rate limit: kitni baar dobara koshish karni hai
LLM_RETRIES = 3

# Alag model pass se claim audit (False karne par ek call kam)
CLAIM_AUDIT = True

# Same sawaal dobara aaye to model call nahi
CACHE_SIZE = 64
_ANSWER_CACHE = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================================
# 2. LLM CALL WITH RATE-LIMIT HANDLING
# ==========================================================

def _is_rate_limit(error):
    rate_limit_class = getattr(groq, "RateLimitError", None)

    if rate_limit_class and isinstance(error, rate_limit_class):
        return True

    return getattr(error, "status_code", None) == 429


def _retry_delay(error, attempt):
    """retry-after header ho to wahi, warna 2, 4, 8 second."""
    try:
        headers = error.response.headers
        value = headers.get("retry-after")

        if value:
            return min(float(value), 30.0)
    except Exception:
        pass

    return min(2.0 * (2 ** attempt), 30.0)


def call_llm(messages, temperature):
    """Groq call (JSON mode). 429 par backoff ke saath retry."""

    for attempt in range(LLM_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
        except Exception as error:
            if not _is_rate_limit(error) or attempt == LLM_RETRIES:
                raise

            delay = _retry_delay(error, attempt)

            logger.warning(
                "Groq rate limit (429). Retrying in %.1fs (%s/%s)",
                delay,
                attempt + 1,
                LLM_RETRIES
            )

            time.sleep(delay)


# ==========================================================
# 3. LOAD FULL SCRIPTURE DATASET
# ==========================================================

def load_scripture_dataset():
    """
    Full verse dataset load karo.

    Pehle env var DATASET_PATH, phir common jagah. Supported formats:
    list of records, ya {"verses"/"data"/"records": [...]}.
    """

    possible_paths = []

    if os.getenv("DATASET_PATH"):
        possible_paths.append(Path(os.getenv("DATASET_PATH")))

    possible_paths += [
        DATA_DIR / "verse_dataset.json",
        DATA_DIR / "clean_dataset.json",
        DATA_DIR / "parsed.json",
        DATA_DIR / "sample_data.json",
        DATA_DIR / "parsed_test.json",
        PROJECT_DIR / "verse_dataset.json"
    ]

    for path in possible_paths:
        if not path.exists():
            continue

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                for key in ("verses", "data", "records"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break

            if isinstance(data, list):
                logger.info(
                    "Loaded %s scripture records from %s",
                    len(data),
                    path
                )
                return data

        except (OSError, json.JSONDecodeError) as error:
            logger.warning(
                "Could not load dataset %s: %s",
                path,
                error
            )

    logger.warning(
        "Full verse dataset was not found. "
        "Using retrieved chunks only."
    )
    return []


SCRIPTURE_RECORDS = load_scripture_dataset()


# ==========================================================
# 4. TEXT AND REFERENCE NORMALIZATION
# ==========================================================

def normalize_text(text):
    """Comparison ke liye text normalize karo (punctuation -> space)."""

    if not isinstance(text, str):
        return ""

    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_reference(reference):
    """
    '2.63', 'BG 2.63', 'Bhagavad Gita 2.63' -> '2.63'
    (grouped '2.3-4' ho to pehla verse '2.3')
    """

    if not isinstance(reference, str):
        return None

    match = re.search(
        r"(?:(?:bhagavad\s*gita|bg)\s*)?"
        r"(\d{1,2})\s*\.\s*(\d{1,3})",
        reference.strip(),
        flags=re.IGNORECASE
    )

    if not match:
        return None

    chapter, verse = match.groups()
    return f"{int(chapter)}.{int(verse)}"


def extract_references(text):
    """Text se chapter.verse references nikalo."""

    if not isinstance(text, str):
        return []

    pattern = (
        r"(?:(?:Bhagavad\s*Gita|BG)\s*)?"
        r"\d{1,2}\s*\.\s*\d{1,3}"
    )

    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    references = []

    for match in matches:
        normalized = normalize_reference(match)

        if normalized and normalized not in references:
            references.append(normalized)

    return references


def _as_text(value):
    """str ya {"text": "..."} dono se text nikalo."""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in ("text", "content", "value"):
            item = value.get(key)

            if isinstance(item, str) and item.strip():
                return item.strip()

    return ""


def get_record_field(record, possible_fields):
    """Pehla non-empty matching field (str ya {"text": ...})."""

    if not isinstance(record, dict):
        return ""

    for field in possible_fields:
        text = _as_text(record.get(field))

        if text:
            return text

    return ""


def get_translation(record):
    return get_record_field(
        record,
        ["translation", "text", "verse_text", "english_translation"]
    )


def get_purport(record):
    return get_record_field(
        record,
        ["purport", "commentary", "explanation"]
    )


def record_references(record):
    """
    Record jin verses ko cover karta hai: ['2.3'] ya grouped ke liye ['2.3', '2.4'].
    Pehla item primary reference hota hai.
    """

    if not isinstance(record, dict):
        return []

    chapter = record.get("chapter") or record.get("chapter_number")
    verse = (
        record.get("verse_label")
        or record.get("verse")
        or record.get("verse_number")
    )

    if chapter is not None and verse is not None:
        match = re.match(
            r"\s*(\d+)(?:\s*[-–—]\s*(\d+))?\s*$",
            str(verse)
        )

        try:
            chapter_number = int(chapter)
        except (TypeError, ValueError):
            chapter_number = None

        if match and chapter_number:
            first = int(match.group(1))
            last = int(match.group(2) or first)

            try:
                last = max(last, int(record.get("verse_end") or last))
            except (TypeError, ValueError):
                pass

            if last - first > 30:
                last = first

            return [f"{chapter_number}.{n}" for n in range(first, last + 1)]

    reference = (
        record.get("reference")
        or record.get("ref")
        or record.get("verse_reference")
    )

    normalized = normalize_reference(str(reference or ""))

    return [normalized] if normalized else []


def get_reference_from_record(record):
    references = record_references(record)
    return references[0] if references else None


SCRIPTURE_INDEX = {}

for _record in SCRIPTURE_RECORDS:
    for _reference in record_references(_record):
        SCRIPTURE_INDEX.setdefault(_reference, _record)


# ==========================================================
# 5. FULL VERSE LOOKUP
# ==========================================================

def find_full_record(reference):
    """Chapter.verse se full record (grouped verses ke dono numbers se)."""

    normalized = normalize_reference(reference)

    if not normalized:
        return None

    return SCRIPTURE_INDEX.get(normalized)


# ==========================================================
# 6. SOURCE IDENTIFICATION
# ==========================================================

def identify_source(document, full_record):
    """
    Retrieved chunk translation hai ya purport.
    Metadata pehle, text matching fallback.
    """

    if not isinstance(document, dict):
        return "unknown"

    for field in ("source_type", "content_type", "section", "field", "type"):
        value = document.get(field)

        if not isinstance(value, str):
            continue

        value = value.lower()

        if "purport" in value or "commentary" in value:
            return "purport"

        if "translation" in value:
            return "translation"

    chunk = (
        document.get("text")
        or document.get("content")
        or document.get("document")
        or ""
    )

    normalized_chunk = normalize_text(chunk)

    if not normalized_chunk or not isinstance(full_record, dict):
        return "unknown"

    translation = normalize_text(get_translation(full_record))
    purport = normalize_text(get_purport(full_record))

    if translation and normalized_chunk in translation:
        return "translation"

    if purport and normalized_chunk in purport:
        return "purport"

    if translation and translation in normalized_chunk:
        return "translation"

    if purport and purport in normalized_chunk:
        return "purport"

    return "unknown"


def supplied_source_types(full_record, fallback_type="unknown"):
    """Model ko kaun se source fields diye ja rahe hain."""

    types = []

    if full_record:
        if get_translation(full_record):
            types.append("translation")

        if get_purport(full_record):
            types.append("purport")

    if not types and fallback_type != "unknown":
        types.append(fallback_type)

    return types


# ==========================================================
# 7. PREPARE VERSES
# ==========================================================

def verse_from_record(reference, full_record, document=None, chunk_text=""):
    """Ek verse object (UI aur model dono ke liye)."""

    document = document or {}
    record = full_record if isinstance(full_record, dict) else None

    source = (
        document.get("source")
        or (record or {}).get("source")
        or DISPLAY_NAME
    )

    covers = record_references(record) if record else [reference]
    primary = covers[0] if covers else reference

    ref_label = primary

    if len(covers) > 1:
        ref_label = f"{covers[0]}-{covers[-1].split('.')[1]}"

    word_meanings = []

    if record and isinstance(record.get("word_meanings"), list):
        word_meanings = record["word_meanings"]

    return {
        "reference": f"{source} {ref_label}",
        "chapter_verse": primary,
        "ref_label": ref_label,
        "covers": covers or [reference],
        "text": get_translation(record) if record else chunk_text,
        "text_is_chunk": record is None,
        "sanskrit": (
            get_record_field(record, ["sanskrit", "devanagari"])
            if record else document.get("sanskrit", "")
        ),
        "transliteration": (
            get_record_field(record, ["transliteration"])
            if record else document.get("transliteration", "")
        ),
        "word_meanings": word_meanings,
        "purport": get_purport(record) if record else "",
        "purport_supplied": "",
        "purport_truncated": False,
        "source_types": [],
        "retrieved_chunks": [],
        "score": None,
        "distance": None
    }


def prepare_verses(results):
    """
    Retrieval results -> verse objects.
    Ek verse ke kai chunks aaye to ek hi verse object mein jude rehte hain.
    """

    verses_by_key = {}

    for result in results:
        if not isinstance(result, dict):
            continue

        document = result.get("document", result)

        if not isinstance(document, dict):
            continue

        chapter = document.get("chapter")
        verse_number = document.get("verse")

        if chapter is None or verse_number is None:
            reference = normalize_reference(
                str(document.get("reference", ""))
            )
        else:
            reference = normalize_reference(f"{chapter}.{verse_number}")

        if not reference:
            continue

        full_record = find_full_record(reference)
        source_type = identify_source(document, full_record)

        chunk_text = (
            document.get("text")
            or document.get("content")
            or ""
        )

        key = (
            get_reference_from_record(full_record)
            if full_record else reference
        ) or reference

        if key not in verses_by_key:
            verse = verse_from_record(
                reference, full_record, document, chunk_text
            )
            verse["score"] = result.get("score")
            verse["distance"] = result.get("distance")
            verses_by_key[key] = verse

        verse_data = verses_by_key[key]

        for supplied in supplied_source_types(full_record, source_type):
            if supplied not in verse_data["source_types"]:
                verse_data["source_types"].append(supplied)

        verse_data["retrieved_chunks"].append({
            "text": chunk_text,
            "source_type": source_type,
            "score": result.get("score"),
            "distance": result.get("distance")
        })

    return list(verses_by_key.values())


def lookup_requested_verses(question):
    """Sawaal mein likhe verse numbers (jaise 2.47) seedha dataset se."""

    found = []
    seen = set()

    for reference in extract_references(question):
        record = find_full_record(reference)

        if not record:
            continue

        verse = verse_from_record(reference, record)

        if verse["chapter_verse"] in seen:
            continue

        seen.add(verse["chapter_verse"])
        verse["source_types"] = supplied_source_types(record)
        found.append(verse)

    return found


ONLY_PATTERN = re.compile(
    r"\b(?:using|from|with|use|based\s+on)\s+only\b"
    r"|\bonly\s+(?:from|using|use|the\s+verses?|verses?|bg|bhagavad|\d)",
    re.IGNORECASE
)


def merge_requested(requested, retrieved, question):
    """Maange gaye verses pehle; 'using only ...' par sirf wahi."""

    if not requested:
        return retrieved

    if ONLY_PATTERN.search(question):
        return requested

    seen = {verse["chapter_verse"] for verse in requested}

    return requested + [
        verse for verse in retrieved
        if verse["chapter_verse"] not in seen
    ]


# ==========================================================
# 8. CONTEXT FOR THE MODEL
# ==========================================================

def _shorten(text, limit):
    """Sentence ya paragraph ki seema par kaato."""

    if len(text) <= limit:
        return text

    cut = text[:limit]
    boundary = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("\n\n"))

    if boundary > limit * 0.6:
        cut = cut[:boundary + 1]

    return cut.rstrip()


def apply_context_budget(verses, preserve_full_purports=False):
    """Context ko MAX_CONTEXT_CHARS ke andar rakho (purports chhoti karke)."""

    base = sum(len(verse.get("text", "")) for verse in verses)
    with_purport = [verse for verse in verses if verse.get("purport")]

    limit = MAX_PURPORT_CHARS

    if with_purport:
        share = max(MAX_CONTEXT_CHARS - base, 0) // len(with_purport)
        limit = min(MAX_PURPORT_CHARS, max(share, 1500))

    for verse in verses:
        purport = verse.get("purport", "")
        supplied = purport if preserve_full_purports else _shorten(purport, limit)

        verse["purport_supplied"] = supplied
        verse["purport_truncated"] = len(supplied) < len(purport)


def build_context(verses):
    """
    Model ke liye source-labelled context.
    Retrieved chunk tabhi alag se jaata hai jab wo translation/purport mein
    pehle se na ho (duplicate text se tokens bachte hain).
    """

    context_parts = []

    for verse in verses:
        parts = [
            f"Reference: {verse['reference']} "
            f"(use \"{verse['chapter_verse']}\" in the reference field)"
        ]

        label = "Retrieved passage" if verse.get("text_is_chunk") else "Translation"

        if verse.get("text"):
            parts.append(f"{label}:\n{verse['text']}")

        purport = verse.get("purport_supplied") or verse.get("purport", "")

        if purport:
            note = " [shortened]" if verse.get("purport_truncated") else ""
            parts.append(f"Purport{note}:\n{purport}")

        shown = normalize_text(verse.get("text", "") + " " + purport)
        extra = []

        for chunk in verse.get("retrieved_chunks", []):
            text = chunk.get("text", "")

            if text and normalize_text(text) not in shown:
                extra.append(
                    f"[Retrieved source: {chunk.get('source_type', 'unknown')}]\n{text}"
                )

        if extra:
            parts.append("Other retrieved passages:\n" + "\n\n".join(extra))

        context_parts.append("\n\n".join(parts))

    return "\n\n---\n\n".join(context_parts)


# ==========================================================
# 9. QUOTE AND POINT VERIFICATION (no model call)
# ==========================================================

def quote_fragments(quote):
    """'a b ... c d' -> ['a b', 'c d'] (normalized, kam se kam 10 chars)."""

    parts = re.split(r"\.{2,}|…", quote or "")
    fragments = [normalize_text(part) for part in parts]

    return [fragment for fragment in fragments if len(fragment) >= 10]


def fragments_in_text(fragments, normalized_text):
    return bool(fragments) and all(
        fragment in normalized_text for fragment in fragments
    )


def _ordered_quote_match(quote, source_text, threshold=0.82):
    """Allow minor punctuation/token differences without accepting loose paraphrases."""
    quote_words = normalize_text(quote).split()
    source_words = normalize_text(source_text).split()

    if len(quote_words) < 4 or not source_words:
        return False

    matched = 0
    cursor = 0
    for word in quote_words:
        try:
            position = source_words.index(word, cursor)
        except ValueError:
            continue
        matched += 1
        cursor = position + 1

    return matched >= 4 and matched / len(quote_words) >= threshold


def locate_quote(quote, verse):
    """
    Identify which supplied source supports a quote.
    Exact normalized matching is preferred; a strict ordered-token fallback
    handles punctuation and small tokenization differences.
    """
    fragments = quote_fragments(quote)
    if not fragments:
        return None

    text_label = "retrieved_passage" if verse.get("text_is_chunk") else "translation"
    candidates = [
        (text_label, verse.get("text", "")),
        ("purport", verse.get("purport_supplied") or verse.get("purport", "")),
    ]

    for label, text in candidates:
        normalized = normalize_text(text)
        if fragments_in_text(fragments, normalized):
            return label
        if _ordered_quote_match(quote, text):
            return label

    chunks = " ".join(
        chunk.get("text", "") for chunk in verse.get("retrieved_chunks", [])
    )
    if fragments_in_text(fragments, normalize_text(chunks)) or _ordered_quote_match(quote, chunks):
        return "retrieved_passage"

    return None


def verse_lookup_by_reference(verses):
    lookup = {}

    for verse in verses or []:
        if not isinstance(verse, dict):
            continue

        for reference in verse.get("covers") or [verse.get("chapter_verse")]:
            ref = normalize_reference(str(reference or ""))

            if ref:
                lookup.setdefault(ref, verse)

    return lookup


def verify_points(points, verses):
    """
    Model ke scriptural_points ko supplied text se verify karo.
    Returns (verified, rejected).
    """

    lookup = verse_lookup_by_reference(verses)
    verified = []
    rejected = []
    seen = set()

    for item in points:
        if not isinstance(item, dict):
            continue

        point = str(item.get("point", "")).strip()
        quote = str(item.get("quote", "")).strip()
        declared = str(item.get("source_type", "")).strip().lower()
        reference = normalize_reference(str(item.get("reference", "")))

        if not point:
            continue

        base = {"point": point, "reference": reference, "quote": quote}

        verse = lookup.get(reference) if reference else None

        if not verse:
            rejected.append({**base, "reason": "reference not in retrieved passages"})
            continue

        source = locate_quote(quote, verse)

        if not source:
            rejected.append({**base, "reason": "quote not found in the supplied text"})
            continue

        signature = (reference, normalize_text(point))

        if signature in seen:
            continue

        seen.add(signature)

        verified.append({
            "point": point,
            "reference": reference,
            "display_reference": f"{DISPLAY_NAME} {verse['ref_label']}",
            "source_type": source,
            "quote": quote,
            "source_corrected": declared in ("translation", "purport") and declared != source
        })

    return verified, rejected


# ==========================================================
# 10. CITATION VALIDATION (reference existence)
# ==========================================================

def validate_citations(answer, citations, verses):
    """
    Generated references retrieved context mein hain ya nahi.
    Sirf reference ka astitva check karta hai, claim ka support nahi.
    """

    retrieved_references = set(verse_lookup_by_reference(verses).keys())

    candidates = []

    if isinstance(citations, list):
        for citation in citations:
            normalized = normalize_reference(str(citation))

            if normalized and normalized not in candidates:
                candidates.append(normalized)

    for reference in extract_references(answer):
        if reference not in candidates:
            candidates.append(reference)

    valid_references = [r for r in candidates if r in retrieved_references]
    invalid_references = [r for r in candidates if r not in retrieved_references]

    return {
        "passed": len(invalid_references) == 0,
        "valid_citations": valid_references,
        "invalid_citations": invalid_references,
        "retrieved_references": sorted(retrieved_references)
    }


# ==========================================================
# 11. CLAIM AUDIT (separate model pass + code checks)
# ==========================================================

CLAIM_STATUSES = {
    "supported",
    "partially_supported",
    "unsupported",
    "practical_suggestion"
}


def overall_status_from_claims(claims):
    """Model ke overall_status par nahi, claims ke status se nikalo."""

    counts = Counter(claim["status"] for claim in claims)

    if not claims:
        return "not_checked", dict(counts)

    if counts["unsupported"] and not (
        counts["supported"] or counts["partially_supported"]
    ):
        return "unsupported", dict(counts)

    if counts["unsupported"] or counts["partially_supported"]:
        return "partially_supported", dict(counts)

    if counts["supported"]:
        return "supported", dict(counts)

    return "practical_only", dict(counts)


AUDIT_PROMPT = """You are a strict evidence auditor. Compare the ANSWER only with the SCRIPTURE EVIDENCE.
Split the answer into its meaningful claims (ignore headings, greetings and style).
For every claim return:
- claim
- status: supported (the evidence says it directly), partially_supported (the evidence says something related or only part of it), unsupported (not in the evidence), or practical_suggestion (everyday advice; every item under "Practical suggestions" is this, unless the evidence itself states it)
- evidence_type: translation, purport, both, or none
- evidence_quote: a short phrase copied word for word from the evidence (max 25 words), or "" if there is none
- evidence_references: list such as ["2.63"]
- explanation: one short sentence
Rules: a verse number alone is not evidence. Do not use outside knowledge. Do not invent evidence. If unsure, choose partially_supported or unsupported.
Return valid JSON only: {"claims": [ ... ]}"""


def validate_claim_support(answer, verses, cited_references):
    """
    Alag model pass se har claim ka support check. Phir code se:
    quote text mein hai? reference retrieved hai? Nahi to 'supported' ghatao.
    Overall status claims se nikalta hai.
    """

    if not isinstance(answer, str) or not answer.strip():
        return {
            "status": "not_checked",
            "counts": {},
            "claims": [],
            "note": "Answer is empty."
        }

    cited = set(cited_references or [])
    lookup = verse_lookup_by_reference(verses)

    audit_verses = []

    for verse in verses:
        if cited & set(verse.get("covers", [])):
            audit_verses.append(verse)

    if not audit_verses:
        audit_verses = verses

    context = build_context(audit_verses)
    normalized_context = normalize_text(context)

    user_prompt = (
        f"SCRIPTURE EVIDENCE:\n{context}\n\nANSWER TO AUDIT:\n{answer}"
    )

    try:
        response = call_llm(
            [
                {"role": "system", "content": AUDIT_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        data = json.loads(response.choices[0].message.content or "{}")
        raw_claims = data.get("claims", [])

        if not isinstance(raw_claims, list):
            raw_claims = []

    except Exception as error:
        logger.warning("Claim-support check unavailable: %s", error)
        return {
            "status": "not_checked",
            "counts": {},
            "claims": [],
            "note": "Claim-support check failed; reference validation is separate."
        }

    cleaned = []

    for item in raw_claims:
        if not isinstance(item, dict):
            continue

        status = item.get("status", "partially_supported")

        if status not in CLAIM_STATUSES:
            status = "partially_supported"

        refs = item.get("evidence_references", [])

        if not isinstance(refs, list):
            refs = []

        normalized_refs = []

        for ref in refs:
            normalized = normalize_reference(str(ref))

            if normalized and normalized in lookup and normalized not in normalized_refs:
                normalized_refs.append(normalized)

        quote = str(item.get("evidence_quote", "") or "")
        fragments = quote_fragments(quote)
        quote_verified = fragments_in_text(fragments, normalized_context)

        evidence_type = str(item.get("evidence_type", "none")).lower()

        if evidence_type not in ("translation", "purport", "both", "none"):
            evidence_type = "none"

        explanation = str(item.get("explanation", ""))

        # 'supported' tabhi jab asli evidence mile
        if status == "supported" and not (normalized_refs and quote_verified):
            status = "partially_supported"
            explanation = (
                explanation + " (Downgraded: the quoted evidence or its "
                "reference could not be matched to the supplied text.)"
            ).strip()

        cleaned.append({
            "claim": str(item.get("claim", "")),
            "status": status,
            "evidence_type": evidence_type,
            "evidence_quote": quote if quote_verified else "",
            "quote_verified": quote_verified,
            "evidence_references": normalized_refs,
            "explanation": explanation
        })

    overall, counts = overall_status_from_claims(cleaned)

    return {
        "status": overall,
        "counts": counts,
        "claims": cleaned,
        "note": (
            "Automated model-based screening; verify important "
            "claims against the source text."
        )
    }


def attach_claim_evidence_details(claim_validation, verses):
    """Audited claims ke saath retrieved scripture details (UI ke liye)."""

    if not isinstance(claim_validation, dict):
        return claim_validation

    claims = claim_validation.get("claims", [])

    if not isinstance(claims, list):
        return claim_validation

    lookup = verse_lookup_by_reference(verses)

    for claim in claims:
        if not isinstance(claim, dict):
            continue

        evidence = []

        for ref in claim.get("evidence_references", []):
            verse = lookup.get(ref)

            if verse:
                evidence.append({
                    "reference": verse.get("reference", f"{DISPLAY_NAME} {ref}"),
                    "chapter_verse": ref,
                    "sanskrit": verse.get("sanskrit", ""),
                    "transliteration": verse.get("transliteration", ""),
                    "translation": verse.get("text", ""),
                    "purport": verse.get("purport", ""),
                    "source_types": verse.get("source_types", []),
                })

        claim["evidence"] = evidence

    return claim_validation


# ==========================================================
# 12. PROMPTS AND ANSWER COMPOSITION
# ==========================================================

DETAIL_PATTERN = re.compile(
    r"\b(in\s+detail|detailed|elaborate|in[\s-]depth|comprehensive|"
    r"complete\s+purport|full\s+purport|explain\s+fully|step\s+by\s+step)\b",
    re.IGNORECASE
)


def wants_detail(question):
    return bool(DETAIL_PATTERN.search(question or ""))


def build_system_prompt(max_points, max_tips):
    return f"""You are VedaVerse AI, a respectful spiritual assistant. Answer ONLY from the scripture passages supplied in the context.

Return ONE JSON object with exactly these keys:
{{
  "summary": "1-2 simple sentences",
  "scriptural_points": [
    {{"point": "...", "reference": "2.63", "source_type": "translation", "quote": "..."}}
  ],
  "practical_suggestions": ["..."],
  "insufficient_context": false,
  "limitations": ""
}}

Rules:
1. Every item in scriptural_points must be something the supplied text actually says. "reference" is a chapter.verse number that appears in the context. "quote" must be copied WORD FOR WORD from that verse's Translation (source_type "translation") or its Purport (source_type "purport"): 6 to 25 words. Never paraphrase inside quote. Use "..." to skip words.
2. "point" explains in simple language what the quote teaches about the question. Do not add ideas that are not in the quote.
3. The translation is the verse's meaning; the purport is the commentary. Never present purport ideas as the verse's own words.
4. Practices such as japa, prayer, mantras, meditation or rituals may go into scriptural_points ONLY if the supplied text mentions them. Everyday advice that the text does not state goes into practical_suggestions, which are NOT scripture. Keep practical_suggestions short and mark nothing in them as scriptural.
5. Never invent verses, quotations, Sanskrit or purport text. Only use references present in the context.
6. "summary" may only restate the scriptural_points: no new claims and no references.
7. If the context does not contain enough to answer, set insufficient_context to true, leave scriptural_points empty (or keep only the ones that truly apply) and explain briefly in limitations. Do not guess.
8. At most {max_points} scriptural_points and {max_tips} practical_suggestions.
9. Beginner-friendly language. Do not present an interpretation as the only possible one.

Return JSON only, with no Markdown fences."""


SOURCE_LABELS = {
    "translation": "translation",
    "purport": "purport",
    "retrieved_passage": "retrieved passage"
}



def extract_display_passage(verse, source_type, quote=""):
    """Translation poori dikhaye; purport mein sirf quote se matching paragraph."""
    if source_type == "translation":
        return verse.get("text", "") or ""

    if source_type == "purport":
        purport = verse.get("purport", "") or ""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", purport) if p.strip()]
        if not paragraphs:
            return purport.strip()

        quote_norm = normalize_text(quote)
        if quote_norm:
            for paragraph in paragraphs:
                if quote_norm in normalize_text(paragraph):
                    return paragraph

            # Quote may be a short fragment; choose the paragraph with the
            # greatest word overlap rather than showing the entire purport.
            quote_words = set(quote_norm.split())
            if quote_words:
                best = max(
                    paragraphs,
                    key=lambda p: len(quote_words & set(normalize_text(p).split()))
                )
                if len(quote_words & set(normalize_text(best).split())) >= min(3, len(quote_words)):
                    return best

        return paragraphs[0]

    return quote or verse.get("text", "") or ""


def build_display_items(points, verses):
    """Simple answer cards plus full verse data for the expand/collapse UI."""
    lookup = verse_lookup_by_reference(verses)
    items = []

    for point in points:
        ref = point.get("reference")
        verse = lookup.get(ref)
        if not verse:
            continue

        source_type = point.get("source_type", "translation")
        items.append({
            "reference": f"BG {verse.get('ref_label', ref)}",
            "chapter_verse": ref,
            "source_type": source_type,
            "heading": f"BG {verse.get('ref_label', ref)} — {source_type}",
            "display_text": extract_display_passage(
                verse, source_type, point.get("quote", "")
            ),
            "full_verse": {
                "sanskrit": verse.get("sanskrit", ""),
                "transliteration": verse.get("transliteration", ""),
                "word_meanings": verse.get("word_meanings", []),
                "translation": verse.get("text", ""),
                "purport": verse.get("purport", ""),
            }
        })

    unique_items = []
    seen_items = set()
    for item in items:
        signature = (
            item["chapter_verse"],
            item["source_type"],
            normalize_text(item["display_text"]),
        )
        if signature not in seen_items:
            seen_items.add(signature)
            unique_items.append(item)
    return unique_items


def compose_answer(summary, points, suggestions, limitations):
    """Verified points se answer banao (source har point ke saath)."""

    blocks = []

    if summary:
        blocks.append(summary)

    if points:
        lines = ["**What the scripture says**"]

        for item in points:
            label = SOURCE_LABELS.get(item["source_type"], item["source_type"])
            lines.append(
                f"- {item['point']} *({item['display_reference']}, {label})*"
            )

        blocks.append("\n".join(lines))

    if suggestions:
        lines = [
            "**Practical suggestions** "
            "*(general advice, not stated in the scripture)*"
        ]

        for tip in suggestions:
            lines.append(f"- {tip}")

        blocks.append("\n".join(lines))

    if limitations:
        blocks.append(f"*Note: {limitations}*")

    return "\n\n".join(blocks)


def build_insufficient_answer(limitations):
    text = (
        "I couldn't find a passage in the available scripture text that "
        "clearly answers this question, so I won't guess."
    )

    if limitations:
        text += f"\n\n*{limitations}*"

    return text


# ==========================================================
# 13. SOURCE SUMMARY
# ==========================================================

def build_source_summary(verses):
    """Kaun se source fields model ko diye gaye (use hone ka proof nahi)."""

    summary = []

    for verse in verses:
        source_types = verse.get("source_types", [])

        if "translation" in source_types and "purport" in source_types:
            label = "Translation and purport provided"
        elif "translation" in source_types:
            label = "Translation provided"
        elif "purport" in source_types:
            label = "Purport provided"
        else:
            label = "Source not identified"

        summary.append({
            "reference": verse["reference"],
            "source_types": source_types,
            "source_label": label,
            "retrieved_chunks": verse.get("retrieved_chunks", [])
        })

    return summary


# ==========================================================
# 14. GENERATE ANSWER
# ==========================================================

def _empty_result(message, **extra):
    result = {
        "answer": message,
        "references": [],
        "invalid_references": [],
        "verses": [],
        "sources": [],
        "model_source_usage": [],
        "scriptural_points": [],
        "practical_suggestions": [],
        "rejected_points": [],
        "insufficient_context": False,
        "validation_passed": False,
        "validation": {},
        "claim_validation": {
            "status": "not_checked",
            "counts": {},
            "claims": [],
            "note": ""
        }
    }
    result.update(extra)
    return result


def _cache_get(key):
    cached = _ANSWER_CACHE.get(key)
    return copy.deepcopy(cached) if cached else None


def _cache_put(key, result):
    if len(_ANSWER_CACHE) >= CACHE_SIZE:
        _ANSWER_CACHE.pop(next(iter(_ANSWER_CACHE)))

    _ANSWER_CACHE[key] = copy.deepcopy(result)


def generate_answer(question, detailed=None):
    """
    Main RAG function.

    detailed=None  -> sawaal mein "in detail" jaisa kuch ho to lamba, warna concise
    detailed=True  -> lamba (zyada points)
    detailed=False -> concise

    Steps: retrieve -> (exact verse lookup) -> context -> structured answer ->
    quote verification -> compose -> reference check.
    """

    if not isinstance(question, str):
        question = ""

    question = question.strip()

    if not question:
        return _empty_result("Please enter a question.")

    detailed = wants_detail(question) if detailed is None else bool(detailed)
    cache_key = (normalize_text(question), detailed)

    cached = _cache_get(cache_key)

    if cached:
        return cached

    try:
        results = retrieve_verses(question, k=TOP_K)
        requested = lookup_requested_verses(question)

        if not results and not requested:
            return _empty_result(
                "I could not find relevant passages in "
                "the available scriptures. Please try "
                "asking your question differently."
            )

        retrieved = prepare_verses(results) if results else []
        verses = merge_requested(requested, retrieved, question)

        if not verses:
            return _empty_result(
                "The retriever returned results, but I "
                "could not extract their verse details. "
                "Please check retrieve.py and the metadata."
            )

        apply_context_budget(verses)
        context = build_context(verses)

        max_points = MAX_POINTS_DETAILED if detailed else MAX_POINTS_CONCISE
        max_tips = MAX_TIPS_DETAILED if detailed else MAX_TIPS_CONCISE

        completion = call_llm(
            [
                {
                    "role": "system",
                    "content": build_system_prompt(max_points, max_tips)
                },
                {
                    "role": "user",
                    "content": (
                        f"Scripture context:\n\n{context}\n\n"
                        f"User question:\n{question}\n\n"
                        "Return the JSON object described in the instructions."
                    )
                }
            ],
            temperature=0.2
        )

        raw_response = completion.choices[0].message.content

        try:
            generated = json.loads(raw_response)

            if not isinstance(generated, dict):
                raise ValueError("not an object")

        except (json.JSONDecodeError, TypeError, ValueError):
            logger.exception("Could not parse Groq response as JSON.")
            generated = {"insufficient_context": True}

        summary = str(generated.get("summary", "") or "").strip()
        limitations = str(generated.get("limitations", "") or "").strip()
        model_says_insufficient = bool(generated.get("insufficient_context"))

        points_raw = generated.get("scriptural_points", [])

        if not isinstance(points_raw, list):
            points_raw = []

        tips_raw = generated.get("practical_suggestions", [])

        if not isinstance(tips_raw, list):
            tips_raw = []

        tips = [str(tip).strip() for tip in tips_raw if str(tip).strip()][:max_tips]

        # ---- quote verification: bina model call ke ----
        verified, rejected = verify_points(points_raw[:max_points + 2], verses)
        verified = verified[:max_points]

        if rejected:
            logger.info(
                "Removed %s unverified point(s): %s",
                len(rejected),
                [(item["reference"], item["reason"]) for item in rejected]
            )

        insufficient = not verified

        if insufficient:
            answer = build_insufficient_answer(limitations)
            citations = []
            tips = []
        else:
            if model_says_insufficient and not limitations:
                limitations = "The available passages only partly answer this question."

            answer = compose_answer(summary, verified, tips, limitations)
            citations = [item["reference"] for item in verified]

        validation = validate_citations(answer, citations, verses)

        # Claim audit removed from the normal answer flow to keep the app simple.
        claim_validation = {
            "status": "not_checked",
            "counts": {},
            "claims": [],
            "note": "Claim audit is disabled."
        }

        validation["points_verified"] = len(verified)
        validation["points_rejected"] = len(rejected)

        result = {
            "answer": answer,
            "references": list(dict.fromkeys(
                item["reference"] for item in verified
                if item.get("reference") in validation["valid_citations"]
            )),
            "invalid_references": validation["invalid_citations"],
            # Retrieved candidates are not references when none were verified
            # as answering the question. Keep them out of the response/UI.
            "verses": [] if insufficient else verses,
            "sources": [] if insufficient else build_source_summary(verses),
            "model_source_usage": [
                {
                    "reference": item["reference"],
                    "source_type": item["source_type"],
                    "explanation": item["quote"]
                }
                for item in verified
            ],
            "scriptural_points": verified,
            "display_items": build_display_items(verified, verses),
            "practical_suggestions": tips,
            "rejected_points": rejected,
            "insufficient_context": insufficient,
            "detailed": detailed,
            "validation_passed": validation["passed"],
            "validation": validation,
            "claim_validation": claim_validation
        }

        _cache_put(cache_key, result)
        return result

    except Exception as error:
        logger.exception("Error while generating the VedaVerse answer.")

        return _empty_result(
            "Something went wrong while generating "
            "the answer. Please check the terminal "
            "for the error details.",
            claim_validation={
                "status": "not_checked",
                "counts": {},
                "claims": [],
                "note": "Generation failed."
            },
            error=str(error)
        )


# ==========================================================
# 15. TERMINAL TEST
# ==========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("              VEDAVERSE AI")
    print("=" * 60)

    while True:
        question = input(
            "\nAsk VedaVerse AI (or type 'exit'): "
        ).strip()

        if question.lower() in ("exit", "quit"):
            print("Hare Krishna! 🙏")
            break

        result = generate_answer(question)

        print("\n" + "=" * 60)
        print("ANSWER")
        print("=" * 60)
        print(result["answer"])

        print("\n" + "=" * 60)
        print("REFERENCES")
        print("=" * 60)
        print(result["references"])

        if result.get("error"):
            print("Error:", result["error"])
