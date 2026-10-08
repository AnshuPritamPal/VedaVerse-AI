"""Thin wrapper around the shared ``rag.rag`` implementation."""

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
