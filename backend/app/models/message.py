"""Persistent conversation message document."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from bson import ObjectId


@dataclass(frozen=True)
class Message:
    conversation_id: ObjectId
    user_id: ObjectId
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    references: list[Any] = field(default_factory=list)
    verses: list[dict[str, Any]] = field(default_factory=list)
    display_items: list[dict[str, Any]] = field(default_factory=list)
    id: ObjectId = field(default_factory=ObjectId)

    def to_mongo_document(self) -> dict[str, Any]:
        return {
            "_id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "references": self.references,
            "verses": self.verses,
            "display_items": self.display_items,
            "created_at": self.created_at,
        }

    @classmethod
    def from_mongo_document(cls, document: dict[str, Any]) -> "Message":
        return cls(
            id=document["_id"],
            conversation_id=document["conversation_id"],
            user_id=document["user_id"],
            role=document["role"],
            content=document["content"],
            references=document.get("references", []),
            verses=document.get("verses", []),
            display_items=document.get("display_items", []),
            created_at=document["created_at"],
        )
