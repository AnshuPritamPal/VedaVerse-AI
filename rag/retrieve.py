
import json
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from .keyword_search import BM25Index, document_text
except ImportError:  # running this file directly as a script
    from keyword_search import BM25Index, document_text


# =========================================================
# 1. CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = VECTORSTORE_DIR / "gita_index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"
VERSE_DATASET_PATH = DATA_DIR / "verse_dataset.json"

MODEL_NAME = "all-MiniLM-L6-v2"

# Hybrid retrieval: how many candidates each retriever contributes, and the
# Reciprocal Rank Fusion constant. A smaller constant lets a retriever's top
# hits count for more; 20 scored best in scripts/eval_retrieval.py (60, the
# value from the original RRF paper, dropped a Sanskrit-term question).
HYBRID_CANDIDATES = 50
RRF_K = 20
SEMANTIC_WEIGHT = 1.0
KEYWORD_WEIGHT = 1.0


# =========================================================
# 2. LOAD FAISS INDEX AND METADATA
# =========================================================

print("Loading FAISS index...")

if not INDEX_PATH.exists():
    raise FileNotFoundError(
        f"FAISS index not found: {INDEX_PATH}\n"
        "Run rag/ingest.py to build the index."
    )

if not METADATA_PATH.exists():
    raise FileNotFoundError(
        f"Metadata file not found: {METADATA_PATH}\n"
        "Run rag/ingest.py to generate metadata."
    )

index = faiss.read_index(str(INDEX_PATH))

with open(METADATA_PATH, "r", encoding="utf-8") as file:
    documents = json.load(file)

if not isinstance(documents, list):
    raise ValueError("metadata.json must contain a list.")

if index.ntotal != len(documents):
    raise ValueError(
        f"Mismatch: FAISS has {index.ntotal} vectors, "
        f"but metadata has {len(documents)} documents."
    )

print(f"Loaded {index.ntotal} indexed documents.")


# =========================================================
# 3. LOAD COMPLETE SCRIPTURE DATASET
# =========================================================

if not VERSE_DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Verse dataset not found: {VERSE_DATASET_PATH}"
    )

with open(VERSE_DATASET_PATH, "r", encoding="utf-8") as file:
    verse_records = json.load(file)

if not isinstance(verse_records, list):
    raise ValueError(
        "verse_dataset.json must contain a list of records."
    )

# Store each complete verse by its chapter and verse number.
verse_lookup = {}

for record in verse_records:
    if not isinstance(record, dict):
        continue

    try:
        chapter = int(record["chapter"])
        verse = int(record["verse"])
    except (KeyError, TypeError, ValueError):
        continue

    if 1 <= chapter <= 18 and verse >= 1:
        verse_lookup[(chapter, verse)] = record

print(f"Loaded {len(verse_lookup)} complete scripture records.")


# =========================================================
# 4. LOAD EMBEDDING MODEL
# =========================================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Building keyword (BM25) index...")

keyword_index = BM25Index([document_text(document) for document in documents])


def embed_texts(texts):
    """Normalized embeddings, so a dot product is cosine similarity."""
    return model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ).astype("float32")


# =========================================================
# 5. REFERENCE HELPERS
# =========================================================

REFERENCE_PATTERN = re.compile(
    r"(?:Bhagavad[\s-]*Gita|BG)\s*"
    r"(\d{1,2})\s*[.:]\s*(\d{1,3})",
    re.IGNORECASE
)

BARE_REFERENCE_PATTERN = re.compile(
    r"(?<!\d)(\d{1,2})\s*[.:]\s*(\d{1,3})(?!\d)"
)


def get_reference(document):
    """Extract a structured Bhagavad Gita reference."""

    if not isinstance(document, dict):
        return None, None, None

    chapter = document.get("chapter")
    verse = document.get("verse")

    metadata = document.get("metadata")

    if isinstance(metadata, dict):
        if chapter is None:
            chapter = metadata.get("chapter")
        if verse is None:
            verse = metadata.get("verse")

    try:
        if chapter is not None and verse is not None:
            chapter_num = int(chapter)
            verse_num = int(verse)

            if 1 <= chapter_num <= 18 and verse_num >= 1:
                return (
                    chapter_num,
                    verse_num,
                    f"Bhagavad Gita {chapter_num}.{verse_num}"
                )
    except (TypeError, ValueError):
        pass

    candidates = [
        document.get("reference"),
        document.get("verse_reference"),
    ]

    if isinstance(metadata, dict):
        candidates.extend([
            metadata.get("reference"),
            metadata.get("verse_reference"),
        ])

    for value in candidates:
        if not isinstance(value, str):
            continue

        match = REFERENCE_PATTERN.search(value)

        if match:
            chapter_num, verse_num = map(int, match.groups())

            if 1 <= chapter_num <= 18 and verse_num >= 1:
                return (
                    chapter_num,
                    verse_num,
                    f"Bhagavad Gita {chapter_num}.{verse_num}"
                )

    return None, None, None


def detect_exact_reference(question):
    """
    Detect a specific verse requested by the user.

    Supports:
        Bhagavad Gita 3.37
        BG 2:47
        Explain 3.37
        Explain verse 3.37
        What does chapter 2 verse 47 teach?
    """

    if not isinstance(question, str):
        return None

    # Explicit book or BG reference.
    match = REFERENCE_PATTERN.search(question)

    if match:
        chapter, verse = map(int, match.groups())
        if 1 <= chapter <= 18 and verse >= 1:
            return chapter, verse

    # Natural-language chapter and verse format.
    chapter_verse = re.search(
        r"\bchapter\s+(\d{1,2})\s+"
        r"(?:,?\s*)verse\s+(\d{1,3})\b",
        question,
        re.IGNORECASE
    )

    if chapter_verse:
        chapter, verse = map(int, chapter_verse.groups())
        if 1 <= chapter <= 18 and verse >= 1:
            return chapter, verse

    # Bare reference such as "Explain 3.37".
    # Only accept it when the question looks like a verse request.
    if re.search(
        r"\b(explain|describe|teach|meaning|purport|translation|"
        r"what does|what is|verse|sloka|shloka)\b",
        question,
        re.IGNORECASE
    ):
        match = BARE_REFERENCE_PATTERN.search(question)

        if match:
            chapter, verse = map(int, match.groups())
            if 1 <= chapter <= 18 and verse >= 1:
                return chapter, verse

    return None


# =========================================================
# 6. DIRECT VERSE LOOKUP
# =========================================================

def retrieve_exact_verse(chapter, verse):
    """
    Retrieve the complete record directly from verse_dataset.json.

    This bypasses FAISS for exact verse questions.
    """

    record = verse_lookup.get((chapter, verse))

    if record is None:
        return []

    reference = record.get(
        "reference",
        f"Bhagavad Gita {chapter}.{verse}"
    )

    return [{
        "document": record,
        "score": 1.0,
        "distance": 0.0,
        "chapter": chapter,
        "verse": verse,
        "reference": reference,
        "retrieval_type": "exact"
    }]


# =========================================================
# 7. SEMANTIC, KEYWORD AND HYBRID SEARCH
# =========================================================

def _build_result(doc_index, score, retrieval_type):
    document = documents[doc_index]
    chapter, verse, reference = get_reference(document)
    return {
        "document": document,
        "score": score,
        "distance": 1.0 - score if retrieval_type == "semantic" else None,
        "chapter": chapter,
        "verse": verse,
        "reference": reference,
        "retrieval_type": retrieval_type
    }


def _unique_verses(results, k):
    """
    The indexes hold chunks, so several top hits may belong to the same verse.
    Keep the best-ranked chunk for each unique verse, preserving rank order.
    """
    unique_results = []
    seen_references = set()
    for result in results:
        reference = result.get("reference")
        key = reference or f"document:{id(result.get('document'))}"
        if key in seen_references:
            continue
        seen_references.add(key)
        unique_results.append(result)
        if len(unique_results) >= k:
            break
    return unique_results


def _semantic_candidates(question, limit):
    """[(doc index, cosine similarity)] from FAISS, best first."""
    if index.ntotal == 0:
        return []
    scores, indices = index.search(embed_texts([question.strip()]), min(limit, index.ntotal))
    return [
        (int(idx), float(score))
        for score, idx in zip(scores[0], indices[0])
        if 0 <= idx < len(documents)
    ]


def retrieve_semantic(
    question,
    k=3,
    min_similarity=None
):
    """Retrieve relevant scripture chunks using FAISS."""

    if min_similarity is not None:
        min_similarity = float(min_similarity)

        if not -1.0 <= min_similarity <= 1.0:
            raise ValueError(
                "min_similarity must be between -1 and 1."
            )

    results = [
        _build_result(doc_index, score, "semantic")
        for doc_index, score in _semantic_candidates(question, max(k * 4, k))
        if min_similarity is None or score >= min_similarity
    ]
    return _unique_verses(results, k)


def retrieve_keyword(question, k=3):
    """Retrieve chunks that share rare terms with the question (BM25)."""
    results = [
        _build_result(doc_index, score, "keyword")
        for doc_index, score in keyword_index.search(question, max(k * 4, k))
    ]
    return _unique_verses(results, k)


def retrieve_hybrid(question, k=3, min_similarity=None):
    """
    Combine semantic and keyword search with Reciprocal Rank Fusion.

    Each retriever ranks its candidates; a chunk scores
    weight / (RRF_K + rank) in every list it appears in. Fusing ranks rather
    than raw scores avoids comparing cosine similarities with BM25 scores,
    which live on unrelated scales.

    min_similarity only filters the semantic list; a strong keyword match can
    still be returned on its own.
    """
    semantic = _semantic_candidates(question, HYBRID_CANDIDATES)
    if min_similarity is not None:
        semantic = [(i, s) for i, s in semantic if s >= float(min_similarity)]
    keyword = keyword_index.search(question, HYBRID_CANDIDATES)

    fused = {}
    for weight, ranked in ((SEMANTIC_WEIGHT, semantic), (KEYWORD_WEIGHT, keyword)):
        for rank, (doc_index, _) in enumerate(ranked, start=1):
            fused[doc_index] = fused.get(doc_index, 0.0) + weight / (RRF_K + rank)

    semantic_scores = dict(semantic)
    keyword_scores = dict(keyword)
    results = []
    for doc_index, rrf_score in sorted(fused.items(), key=lambda item: -item[1]):
        result = _build_result(doc_index, semantic_scores.get(doc_index, 0.0), "hybrid")
        result["distance"] = 1.0 - result["score"]
        result["rrf_score"] = rrf_score
        result["keyword_score"] = keyword_scores.get(doc_index, 0.0)
        results.append(result)
    return _unique_verses(results, k)


# =========================================================
# 8. MAIN RETRIEVAL FUNCTION
# =========================================================

def retrieve_verses(
    question,
    k=3,
    min_similarity=None
):
    """
    Main retrieval entry point.

    Exact verse request:
        Retrieve the complete record directly.

    General question:
        Use hybrid search (semantic FAISS + BM25 keywords).

    If an explicitly requested verse does not exist:
        Return an empty list instead of unrelated results.
    """

    if not isinstance(question, str) or not question.strip():
        return []

    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        return []

    exact_reference = detect_exact_reference(question)

    if exact_reference is not None:
        chapter, verse = exact_reference
        return retrieve_exact_verse(chapter, verse)

    return retrieve_hybrid(
        question=question,
        k=k,
        min_similarity=min_similarity
    )


# =========================================================
# 9. DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print("\n" + "=" * 55)
    print("       VEDAVERSE AI - RETRIEVAL TEST")
    print("=" * 55)

    while True:
        question = input(
            "\nAsk VedaVerse AI (or type 'exit'): "
        ).strip()

        if question.lower() in {"exit", "quit"}:
            break

        results = retrieve_verses(question, k=5)

        print("\nRelevant results:\n")

        if not results:
            print("No matching verse or relevant results found.")
            continue

        for rank, result in enumerate(results, start=1):
            doc = result["document"]

            print(f"\nResult {rank}")
            print(f"Retrieval: {result['retrieval_type']}")
            print(f"Reference: {result['reference']}")
            print(f"Similarity: {result['score']:.4f}")

            if isinstance(doc, dict):
                print("\nTranslation:")
                print(doc.get("translation", ""))

                print("\nPurport:")
                purport = doc.get("purport", "")
                print(purport if purport else "No purport available.")

            print("-" * 55)
