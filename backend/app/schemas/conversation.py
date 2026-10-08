"""Conversation create and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ConversationCreateRequest(BaseModel):
    title: str = Field(default="New Conversation", min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Title cannot be blank.")
        return title


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
