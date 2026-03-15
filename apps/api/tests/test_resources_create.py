"""Tests for POST /resources endpoint (resource creation)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus


class TestCreateResource:
    """Test cases for creating resources."""

    @pytest.mark.asyncio
    async def test_create_url_resource_success(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict
    ):
        """Test creating a URL resource successfully."""
        resource_data = {
            "content_type": "url",
            "original_content": "https://example.com/article",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 202
        data = response.json()

        assert "id" in data
        assert data["content_type"] == "url"
        assert data["original_content"] == "https://example.com/article"
        assert data["status"] == "PENDING"
        assert data["prefer_provider"] is None
        assert data["title"] is None
        assert data["summary"] is None
        assert data["tags"] == []
        assert "created_at" in data
        assert "updated_at" in data

        # Verify resource was created in database
        resource_id = int(data["id"])
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        resource = result.scalar_one_or_none()

        assert resource is not None
        assert resource.content_type == "url"
        assert resource.original_content == "https://example.com/article"
        assert resource.status == ResourceStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_text_resource_success(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict
    ):
        """Test creating a text resource successfully."""
        resource_data = {
            "content_type": "text",
            "original_content": "This is some important text to learn from.",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 202
        data = response.json()

        assert data["content_type"] == "text"
        assert data["original_content"] == "This is some important text to learn from."
        assert data["status"] == "PENDING"

        # Verify database record
        resource_id = int(data["id"])
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        resource = result.scalar_one_or_none()

        assert resource is not None
        assert resource.content_type == "text"
        assert resource.original_content == "This is some important text to learn from."

    @pytest.mark.asyncio
    async def test_create_resource_with_prefer_provider(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict
    ):
        """Test creating a resource with prefer_provider hint."""
        resource_data = {
            "content_type": "url",
            "original_content": "https://arxiv.org/abs/2301.00001",
            "prefer_provider": "academic",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 202
        data = response.json()

        assert data["prefer_provider"] == "academic"

        # Verify database record
        resource_id = int(data["id"])
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        resource = result.scalar_one_or_none()

        assert resource is not None
        assert resource.prefer_provider == "academic"

    @pytest.mark.asyncio
    async def test_create_resource_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests return 401."""
        resource_data = {
            "content_type": "url",
            "original_content": "https://example.com/article",
        }

        response = await client.post("/resources/", json=resource_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_resource_invalid_token(self, client: AsyncClient):
        """Test that invalid token returns 401."""
        resource_data = {
            "content_type": "url",
            "original_content": "https://example.com/article",
        }

        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await client.post(
            "/resources/", json=resource_data, headers=invalid_headers
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_resource_missing_content_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that missing content_type returns validation error."""
        resource_data = {
            "original_content": "https://example.com/article",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_missing_original_content(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that missing original_content returns validation error."""
        resource_data = {
            "content_type": "url",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_empty_original_content(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that empty original_content returns validation error."""
        resource_data = {
            "content_type": "url",
            "original_content": "",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_whitespace_original_content(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that whitespace-only original_content returns validation error."""
        resource_data = {
            "content_type": "text",
            "original_content": "   \n\t   ",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_invalid_content_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that invalid content_type returns validation error."""
        resource_data = {
            "content_type": "invalid",
            "original_content": "Some content",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_resource_ownership(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test that created resource belongs to the authenticated user."""
        resource_data = {
            "content_type": "url",
            "original_content": "https://example.com/test-ownership",
        }

        response = await client.post(
            "/resources/", json=resource_data, headers=auth_headers
        )
        assert response.status_code == 202

        data = response.json()
        assert data["owner_id"] == str(test_user.id)

        # Verify in database
        resource_id = int(data["id"])
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        resource = result.scalar_one_or_none()

        assert resource is not None
        assert resource.owner_id == test_user.id
