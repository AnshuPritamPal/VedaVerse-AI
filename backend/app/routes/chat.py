"""Chat endpoint that delegates answer generation to the existing RAG code."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.services.rag_service import RagServiceError, generate_rag_response


logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    references: list[str]
    verses: list[dict[str, Any]]
    display_items: list[dict[str, Any]]
    validation_passed: bool
    validation: dict[str, Any]
    insufficient_context: bool


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")

    try:
        result = await run_in_threadpool(generate_rag_response, message)
    except RagServiceError as exc:
        logger.exception("RAG service failed while answering a chat request.")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while answering a chat request.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the answer.",
        ) from exc

    return ChatResponse(
        answer=result.get("answer", ""),
        references=result.get("references", []),
        verses=result.get("verses", []),
        display_items=result.get("display_items", []),
        validation_passed=bool(result.get("validation_passed", False)),
        validation=result.get("validation", {}),
        insufficient_context=bool(result.get("insufficient_context", False)),
    )
