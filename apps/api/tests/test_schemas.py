"""Tests for Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from schemas.resource import (
    ContentType,
    ResourceCreate,
    ResourceResponse,
    ResourceStatus,
    ResourceUpdate,
)


class TestResourceCreate:
    """Test ResourceCreate schema."""

    def test_valid_url_resource(self):
        """Test creating a valid URL resource."""
        data = {
            "content_type": "url",
            "original_content": "https://example.com/article",
        }
        resource = ResourceCreate(**data)
        assert resource.content_type == ContentType.URL
        assert resource.original_content == "https://example.com/article"
        assert resource.prefer_provider is None

    def test_valid_text_resource(self):
        """Test creating a valid text resource."""
        data = {
            "content_type": "text",
            "original_content": "This is some sample text content",
        }
        resource = ResourceCreate(**data)
        assert resource.content_type == ContentType.TEXT
        assert resource.original_content == "This is some sample text content"

    def test_with_prefer_provider(self):
        """Test creating a resource with prefer_provider."""
        data = {
            "content_type": "url",
            "original_content": "https://twitter.com/example",
            "prefer_provider": "twitter",
        }
        resource = ResourceCreate(**data)
        assert resource.prefer_provider == "twitter"

    def test_invalid_content_type(self):
        """Test that invalid content_type raises ValidationError."""
        data = {"content_type": "invalid", "original_content": "https://example.com"}
        with pytest.raises(ValidationError):
            ResourceCreate(**data)

    def test_empty_original_content(self):
        """Test that empty original_content raises ValidationError."""
        data = {"content_type": "url", "original_content": ""}
        with pytest.raises(ValidationError):
            ResourceCreate(**data)

    def test_whitespace_original_content(self):
        """Test that whitespace-only original_content raises ValidationError."""
        data = {"content_type": "text", "original_content": "   \n\t  "}
        with pytest.raises(ValidationError):
            ResourceCreate(**data)

    def test_strips_whitespace(self):
        """Test that original_content whitespace is stripped."""
        data = {"content_type": "text", "original_content": "  content with spaces  "}
        resource = ResourceCreate(**data)
        assert resource.original_content == "content with spaces"


class TestResourceUpdate:
    """Test ResourceUpdate schema."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        resource = ResourceUpdate()
        assert resource.title is None
        assert resource.summary is None
        assert resource.tags is None
        assert resource.original_content is None

    def test_partial_update(self):
        """Test updating only some fields."""
        data = {"title": "Updated title", "tags": ["new", "tags"]}
        resource = ResourceUpdate(**data)
        assert resource.title == "Updated title"
        assert resource.tags == ["new", "tags"]
        assert resource.summary is None
        assert resource.original_content is None

    def test_empty_original_content_validation(self):
        """Test that empty original_content raises ValidationError."""
        data = {"original_content": ""}
        with pytest.raises(ValidationError):
            ResourceUpdate(**data)

    def test_strips_original_content_whitespace(self):
        """Test that original_content whitespace is stripped."""
        data = {"original_content": "  updated content  "}
        resource = ResourceUpdate(**data)
        assert resource.original_content == "updated content"


class TestResourceResponse:
    """Test ResourceResponse schema."""

    def test_valid_response(self):
        """Test creating a valid resource response."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "owner_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "content_type": "url",
            "original_content": "https://example.com/article",
            "title": "Example Article",
            "summary": "This is an example article",
            "tags": ["example", "article"],
            "status": "READY",
            "processing_status": "success",
            "embedding_status": "ready",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        resource = ResourceResponse(**data)
        assert resource.id == "550e8400-e29b-41d4-a716-446655440000"
        assert resource.content_type == ContentType.URL
        assert resource.status == ResourceStatus.READY
        assert resource.tags == ["example", "article"]

    def test_minimal_response(self):
        """Test creating a response with minimal required fields."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "owner_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "content_type": "text",
            "original_content": "Some text content",
            "status": "PENDING",
            "processing_status": "pending",
            "embedding_status": "none",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        resource = ResourceResponse(**data)
        assert resource.title is None
        assert resource.summary is None
        assert resource.tags == []
        assert resource.prefer_provider is None

    def test_invalid_status(self):
        """Test that invalid status raises ValidationError."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "owner_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "content_type": "url",
            "original_content": "https://example.com",
            "status": "INVALID_STATUS",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        with pytest.raises(ValidationError):
            ResourceResponse(**data)
