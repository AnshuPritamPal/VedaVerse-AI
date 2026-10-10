"""Thin wrapper around the shared ``rag.rag`` implementation."""

import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Make the root-level RAG package available whether Uvicorn starts from the
# project root or from the backend directory.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class RagServiceError(RuntimeError):
    """Raised when the existing RAG service cannot produce a response."""


def generate_rag_response(message: str) -> dict[str, Any]:
    """Call the project's existing answer pipeline and preserve its result."""
    try:
        from rag.rag import generate_answer

        result = generate_answer(message)
    except Exception as exc:
        raise RagServiceError("The RAG pipeline could not process the message.") from exc

    if not isinstance(result, dict):
        raise RagServiceError("The RAG pipeline returned an invalid response.")
    if result.get("error"):
        raise RagServiceError("The RAG pipeline failed to generate an answer.")

    return result


def question_signature(question: str) -> dict[str, Any]:
    """What the answer cache needs to recognise a repeated question.

    - normalized: case/punctuation-insensitive text for exact matching
    - detailed: "in detail" requests get longer answers, so are cached apart
    - numbers: verse/chapter numbers, which must match exactly (2.47 != 2.48)
    - embedding: normalized MiniLM vector for paraphrase matching
    """
    try:
        from rag.rag import normalize_text, wants_detail
        from rag.retrieve import embed_texts

        embedding = embed_texts([question])[0]
    except Exception as exc:
        raise RagServiceError("The question could not be analysed.") from exc

    return {
        "normalized": normalize_text(question),
        "detailed": wants_detail(question),
        "numbers": re.findall(r"\d+", question),
        "embedding": [float(value) for value in embedding],
    }
