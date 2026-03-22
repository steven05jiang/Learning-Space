"""Pydantic schemas for conversation API endpoints."""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class MessageRole(str, enum.Enum):
    """Valid message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class ConversationCreate(BaseModel):
    """Request schema for creating a new conversation."""

    title: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            return None
        return v.strip() if v else None


class ConversationUpdate(BaseModel):
    """Request schema for updating a conversation."""

    title: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            return None
        return v.strip() if v else None


class ConversationResponse(BaseModel):
    """Response schema for conversation data."""

    id: int
    user_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Request schema for creating a new message."""

    role: MessageRole
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("content cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Response schema for message data."""

    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessagesResponse(BaseModel):
    """Response schema for conversation with its messages."""

    id: int
    user_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Response schema for paginated conversation list."""

    items: list[ConversationResponse]
    total: int
    limit: int
    offset: int