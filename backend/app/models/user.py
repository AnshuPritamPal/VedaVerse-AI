"""User document model stored in MongoDB."""

from dataclasses import dataclass, field
from datetime import datetime

from bson import ObjectId


@dataclass(frozen=True)
class User:
    email: str
    username: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    id: ObjectId = field(default_factory=ObjectId)

    def to_mongo_document(self) -> dict:
        """Serialize the model using MongoDB's conventional ``_id`` field."""
        return {
            "_id": self.id,
            "email": self.email,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_mongo_document(cls, document: dict) -> "User":
        """Build a user model from a MongoDB document."""
        return cls(
            id=document["_id"],
            email=document["email"],
            username=document["username"],
            hashed_password=document["hashed_password"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
