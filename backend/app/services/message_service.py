"""Owner-scoped MongoDB operations for persistent messages."""

from datetime import datetime, timezone
from typing import Any, Literal

from bson import ObjectId
from pymongo import ASCENDING
from pymongo.errors import PyMongoError

from app.database.mongodb import mongodb
from app.models.message import Message


class MessageStoreUnavailable(RuntimeError):
    """Raised when message storage cannot be reached or updated."""


class MessageService:
    def _collection(self):
        if mongodb.database is None:
            raise MessageStoreUnavailable("MongoDB is not connected.")
        return mongodb.database["messages"]

    async def ensure_indexes(self) -> None:
        try:
            await self._collection().create_index(
                [
                    ("user_id", ASCENDING),
                    ("conversation_id", ASCENDING),
                    ("created_at", ASCENDING),
                ],
                name="idx_messages_owner_conversation_created",
            )
        except PyMongoError as exc:
            raise MessageStoreUnavailable("Message index is unavailable.") from exc

    async def create(
        self,
        *,
        conversation_id: ObjectId,
        user_id: ObjectId,
        role: Literal["user", "assistant"],
        content: str,
        references: list[Any] | None = None,
        verses: list[dict[str, Any]] | None = None,
        display_items: list[dict[str, Any]] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            references=references or [],
            verses=verses or [],
            display_items=display_items or [],
            created_at=datetime.now(timezone.utc),
        )
        try:
            await self._collection().insert_one(message.to_mongo_document())
        except PyMongoError as exc:
            raise MessageStoreUnavailable("Message could not be saved.") from exc
        return message

    async def list_for_conversation(
        self, *, conversation_id: ObjectId, user_id: ObjectId
    ) -> list[Message]:
        try:
            cursor = self._collection().find(
                {"conversation_id": conversation_id, "user_id": user_id}
            ).sort("created_at", ASCENDING)
            documents = await cursor.to_list(length=None)
        except PyMongoError as exc:
            raise MessageStoreUnavailable("Messages could not be retrieved.") from exc
        return [Message.from_mongo_document(document) for document in documents]

    async def update_conversation_activity(
        self, *, conversation_id: ObjectId, user_id: ObjectId
    ) -> None:
        """Advance activity time only for a conversation owned by this user."""
        try:
            result = await mongodb.database["conversations"].update_one(
                {"_id": conversation_id, "user_id": user_id},
                {"$set": {"updated_at": datetime.now(timezone.utc)}},
            )
        except PyMongoError as exc:
            raise MessageStoreUnavailable(
                "Conversation activity could not be updated."
            ) from exc
        if result.matched_count != 1:
            raise MessageStoreUnavailable("Conversation could not be updated.")


message_service = MessageService()
