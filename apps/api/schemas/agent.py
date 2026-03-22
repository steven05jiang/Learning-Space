"""Pydantic schemas for agent API endpoints."""

from typing import Any, List, Optional

from pydantic import BaseModel, field_validator


class ConversationMessage(BaseModel):
    """A message in conversation history."""

    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is either 'user' or 'assistant'."""
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("content cannot be empty")
        return v.strip()


class AgentQuery(BaseModel):
    """Request schema for agent query."""

    query: str
    conversation_history: List[ConversationMessage] = []

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("query cannot be empty")
        return v.strip()


class AgentResponse(BaseModel):
    """Response schema for agent query."""

    response: str
    sources: Optional[List[Any]] = None  # Tool call results/sources used


class ToolCallResult(BaseModel):
    """Result from a tool call."""

    tool_name: str
    result: Any
    success: bool
    error: Optional[str] = None
