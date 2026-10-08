"""Persistent conversation document model."""

from dataclasses import dataclass, field
from datetime import datetime

from bson import ObjectId


@dataclass(frozen=True)
class Conversation:
    user_id: ObjectId
    title: str
    created_at: datetime
    updated_at: datetime
    id: ObjectId = field(default_factory=ObjectId)

    def to_mongo_document(self) -> dict:
        """Serialize only the Phase 2.4 conversation fields."""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_mongo_document(cls, document: dict) -> "Conversation":
        return cls(
            id=document["_id"],
            user_id=document["user_id"],
            title=document["title"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
