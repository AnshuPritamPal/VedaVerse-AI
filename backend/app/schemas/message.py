"""Message request and response schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("Message cannot be blank.")
        return content


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    references: list[Any] = Field(default_factory=list)
    verses: list[dict[str, Any]] = Field(default_factory=list)
    display_items: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
