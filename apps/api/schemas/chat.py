"""Pydantic schemas for chat API endpoints."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str
    conversation_id: Optional[UUID] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate that message is not empty and within length limits."""
        if not v or not v.strip():
            raise ValueError("message cannot be empty")

        cleaned_message = v.strip()
        if len(cleaned_message) > 2000:
            raise ValueError("message cannot exceed 2000 characters")

        return cleaned_message


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    conversation_id: UUID
    message_id: UUID
    response: str
    role: str = "assistant"
