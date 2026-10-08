"""Authenticated message history and conversation question endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.core.security import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreateRequest, MessageResponse
from app.services.conversation_service import (
    ConversationStoreUnavailable,
    InvalidConversationId,
    conversation_service,
)
from app.services.message_service import MessageStoreUnavailable, message_service
from app.services.rag_service import RagServiceError, generate_rag_response


logger = logging.getLogger(__name__)
router = APIRouter()


def _message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        role=message.role,
        content=message.content,
        references=message.references,
        verses=message.verses,
        display_items=message.display_items,
        created_at=message.created_at,
    )


def _storage_error(exc: Exception) -> HTTPException:
    logger.error("Message/conversation storage is unavailable: %s", exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Message storage is unavailable.",
    )


async def _owned_conversation(conversation_id: str, user: User) -> Conversation:
    try:
        conversation = await conversation_service.get_for_user(
            conversation_id=conversation_id,
            user_id=user.id,
        )
    except InvalidConversationId as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID.") from exc
    except ConversationStoreUnavailable as exc:
        raise _storage_error(exc) from exc

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["messages"],
)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    conversation = await _owned_conversation(conversation_id, current_user)

    try:
        await message_service.create(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="user",
            content=request.content,
        )
        # Record the user activity even if answer generation subsequently fails.
        await message_service.update_conversation_activity(
            conversation_id=conversation.id,
            user_id=current_user.id,
        )
    except MessageStoreUnavailable as exc:
        raise _storage_error(exc) from exc

    try:
        result = await run_in_threadpool(generate_rag_response, request.content)
    except RagServiceError as exc:
        logger.exception("RAG failed for a persisted conversation message.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The question was saved, but answer generation failed. Please try again.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected failure generating a conversation answer.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The question was saved, but an unexpected answer generation error occurred.",
        ) from exc

    answer = result.get("answer")
    if not isinstance(answer, str):
        logger.error("RAG response did not include an answer string.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The question was saved, but the RAG response was invalid.",
        )

    try:
        assistant_message = await message_service.create(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="assistant",
            content=answer,
            references=result.get("references", []),
            verses=result.get("verses", []),
            display_items=result.get("display_items", []),
        )
        await message_service.update_conversation_activity(
            conversation_id=conversation.id,
            user_id=current_user.id,
        )
    except MessageStoreUnavailable as exc:
        raise _storage_error(exc) from exc

    return _message_response(assistant_message)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    tags=["messages"],
)
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    conversation = await _owned_conversation(conversation_id, current_user)
    try:
        messages = await message_service.list_for_conversation(
            conversation_id=conversation.id,
            user_id=current_user.id,
        )
    except MessageStoreUnavailable as exc:
        raise _storage_error(exc) from exc
    return [_message_response(message) for message in messages]
