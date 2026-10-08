"""Owner-scoped MongoDB operations for persistent conversations."""

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from app.database.mongodb import mongodb
from app.models.conversation import Conversation


class ConversationStoreUnavailable(Exception):
    """Raised when the conversation collection cannot be accessed."""


class InvalidConversationId(Exception):
    """Raised when an identifier is not a valid MongoDB ObjectId."""


class ConversationService:
    def _collection(self):
        if mongodb.database is None:
            raise ConversationStoreUnavailable("MongoDB is not connected.")
        return mongodb.database["conversations"]

    async def ensure_indexes(self) -> None:
        """Index owner lookups and the per-owner updated-time sort."""
        try:
            await self._collection().create_index(
                [("user_id", ASCENDING), ("updated_at", DESCENDING)],
                name="idx_conversations_user_updated",
            )
        except PyMongoError as exc:
            raise ConversationStoreUnavailable(
                "Conversation storage is unavailable."
            ) from exc

    async def create(self, *, user_id: ObjectId, title: str) -> Conversation:
        now = datetime.now(timezone.utc)
        conversation = Conversation(
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        try:
            await self._collection().insert_one(conversation.to_mongo_document())
        except PyMongoError as exc:
            raise ConversationStoreUnavailable(
                "Conversation could not be saved."
            ) from exc
        return conversation

    async def list_for_user(self, *, user_id: ObjectId) -> list[Conversation]:
        try:
            cursor = self._collection().find({"user_id": user_id}).sort(
                "updated_at", DESCENDING
            )
            documents = await cursor.to_list(length=None)
        except PyMongoError as exc:
            raise ConversationStoreUnavailable(
                "Conversations could not be retrieved."
            ) from exc
        return [Conversation.from_mongo_document(document) for document in documents]

    async def get_for_user(
        self, *, conversation_id: str, user_id: ObjectId
    ) -> Conversation | None:
        object_id = self._parse_id(conversation_id)
        try:
            document = await self._collection().find_one(
                {"_id": object_id, "user_id": user_id}
            )
        except PyMongoError as exc:
            raise ConversationStoreUnavailable(
                "Conversation could not be retrieved."
            ) from exc
        return Conversation.from_mongo_document(document) if document else None

    async def delete_for_user(
        self, *, conversation_id: str, user_id: ObjectId
    ) -> bool:
        object_id = self._parse_id(conversation_id)
        try:
            result = await self._collection().delete_one(
                {"_id": object_id, "user_id": user_id}
            )
        except PyMongoError as exc:
            raise ConversationStoreUnavailable(
                "Conversation could not be deleted."
            ) from exc
        return result.deleted_count == 1

    @staticmethod
    def _parse_id(conversation_id: str) -> ObjectId:
        if not ObjectId.is_valid(conversation_id):
            raise InvalidConversationId
        return ObjectId(conversation_id)


conversation_service = ConversationService()
