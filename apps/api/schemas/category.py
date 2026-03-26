"""Pydantic schemas for category API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CategoryCreate(BaseModel):
    """Request schema for creating a new category."""

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty and normalize whitespace."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class CategoryResponse(BaseModel):
    """Response schema for category data."""

    id: int
    name: str
    is_system: bool
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)