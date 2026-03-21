"""Pydantic schemas for resource API endpoints."""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ContentType(str, enum.Enum):
    """Valid content types for resources."""

    URL = "url"
    TEXT = "text"


class ResourceStatus(str, enum.Enum):
    """Resource processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class ResourceCreate(BaseModel):
    """Request schema for creating a new resource."""

    content_type: ContentType
    original_content: str
    prefer_provider: Optional[str] = None

    @field_validator("original_content")
    @classmethod
    def validate_original_content(cls, v: str) -> str:
        """Validate that original_content is not empty."""
        if not v or not v.strip():
            raise ValueError("original_content cannot be empty")
        return v.strip()


class ResourceUpdate(BaseModel):
    """Request schema for updating a resource."""

    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    original_content: Optional[str] = None

    @field_validator("original_content")
    @classmethod
    def validate_original_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate that original_content is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("original_content cannot be empty")
        return v.strip() if v else None


class ResourceResponse(BaseModel):
    """Response schema for resource data."""

    id: str
    owner_id: str
    content_type: ContentType
    original_content: str
    prefer_provider: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: list[str] = []
    status: ResourceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResourceListItem(BaseModel):
    """Response schema for resource list items (reduced fields for listing)."""

    id: str
    url: Optional[str] = None  # Populated from original_content if content_type is URL
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: list[str] = []
    status: ResourceStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResourceNodeItem(BaseModel):
    """Response schema for resource items from graph nodes (includes all required fields)."""

    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    original_content: str
    content_type: ContentType
    status: ResourceStatus
    created_at: datetime
    tags: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class ResourceListResponse(BaseModel):
    """Response schema for paginated resource list."""

    items: list[ResourceListItem]
    total: int
    limit: int
    offset: int


class ResourceNodeResponse(BaseModel):
    """Response schema for paginated resource node list."""

    items: list[ResourceNodeItem]
    total: int
    limit: int
    offset: int
