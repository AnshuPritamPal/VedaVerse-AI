"""Authenticated conversation management endpoints."""

import logging
from dataclasses import replace

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.security import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.conversation import ConversationCreateRequest, ConversationResponse
from app.services.conversation_service import (
    DEFAULT_TITLE,
    ConversationStoreUnavailable,
    InvalidConversationId,
    conversation_service,
    title_from_question,
)
from app.services.message_service import MessageStoreUnavailable, message_service


logger = logging.getLogger(__name__)
router = APIRouter()


def _response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


async def _backfill_title(conversation: Conversation) -> Conversation:
    """Name conversations created before automatic titling from their first question."""
    if conversation.title != DEFAULT_TITLE:
        return conversation
    try:
        first = await message_service.first_user_message(
            conversation_id=conversation.id, user_id=conversation.user_id
        )
        if first is None:
            return conversation
        title = title_from_question(first.content)
        await conversation_service.set_title(
            conversation_id=conversation.id, user_id=conversation.user_id, title=title
        )
    except (MessageStoreUnavailable, ConversationStoreUnavailable):
        logger.warning("Could not backfill a conversation title.")
        return conversation
    return replace(conversation, title=title)


def _storage_error(exc: Exception) -> HTTPException:
    logger.error("Conversation storage is unavailable: %s", exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Conversation storage is unavailable.",
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["conversations"],
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    try:
        conversation = await conversation_service.create(
            user_id=current_user.id,
            title=request.title,
        )
    except ConversationStoreUnavailable as exc:
        raise _storage_error(exc) from exc
    return _response(conversation)


@router.get("", response_model=list[ConversationResponse], tags=["conversations"])
async def list_conversations(
    current_user: User = Depends(get_current_user),
) -> list[ConversationResponse]:
    try:
        conversations = await conversation_service.list_for_user(
            user_id=current_user.id
        )
    except ConversationStoreUnavailable as exc:
        raise _storage_error(exc) from exc
    return [_response(await _backfill_title(conversation)) for conversation in conversations]


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    tags=["conversations"],
)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    try:
        conversation = await conversation_service.get_for_user(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except InvalidConversationId as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID.") from exc
    except ConversationStoreUnavailable as exc:
        raise _storage_error(exc) from exc

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return _response(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["conversations"],
)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        deleted = await conversation_service.delete_for_user(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except InvalidConversationId as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID.") from exc
    except ConversationStoreUnavailable as exc:
        raise _storage_error(exc) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    try:
        await message_service.delete_for_conversation(
            conversation_id=ObjectId(conversation_id), user_id=current_user.id
        )
    except MessageStoreUnavailable:
        logger.warning("Conversation deleted but its messages could not be removed.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
