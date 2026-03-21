"""Tests for graph endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus
from models.user import User


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create a second test user in the database."""
    user = User(
        email="other@example.com",
        display_name="Other User",
        avatar_url="https://example.com/avatar2.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetNodeResources:
    """Test cases for GET /graph/nodes/{node_id}/resources."""

    async def test_get_node_resources_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test successful retrieval of resources for a node."""
        # Create test resources with tags
        resource1 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/1",
            title="Resource 1",
            summary="Summary 1",
            tags=["python", "web"],
            status=ResourceStatus.READY,
        )
        resource2 = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Text content 2",
            title="Resource 2",
            summary="Summary 2",
            tags=["python", "machine-learning"],
            status=ResourceStatus.READY,
        )
        resource3 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/3",
            title="Resource 3",
            summary="Summary 3",
            tags=["javascript", "web"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([resource1, resource2, resource3])
        await db_session.commit()

        # Get resources for "python" tag
        response = await client.get(
            "/graph/nodes/python/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 2 resources with "python" tag
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Check that both resources are returned
        resource_ids = [item["id"] for item in data["items"]]
        assert str(resource1.id) in resource_ids
        assert str(resource2.id) in resource_ids
        assert str(resource3.id) not in resource_ids

        # Verify resource structure
        for item in data["items"]:
            assert "id" in item
            assert "title" in item
            assert "summary" in item
            assert "tags" in item
            assert "status" in item
            assert "created_at" in item
            assert "python" in item["tags"]

    async def test_get_node_resources_empty_result(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test retrieval when no resources match the tag."""
        # Create a resource without the searched tag
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="Resource",
            summary="Summary",
            tags=["different-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/nonexistent-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0
        assert data["limit"] == 0
        assert data["offset"] == 0

    async def test_get_node_resources_owner_scoped(
        self,
        client: AsyncClient,
        test_user: User,
        other_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that resources are scoped to the authenticated user."""
        # Create resources for both users with same tag
        user_resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/user",
            title="User Resource",
            tags=["shared-tag"],
            status=ResourceStatus.READY,
        )
        other_resource = Resource(
            owner_id=other_user.id,
            content_type="url",
            original_content="https://example.com/other",
            title="Other Resource",
            tags=["shared-tag"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([user_resource, other_resource])
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/shared-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only return the authenticated user's resource
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(user_resource.id)
        assert data["items"][0]["title"] == "User Resource"

    async def test_get_node_resources_url_field(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that url field is populated correctly for URL content type."""
        # Create URL and text resources
        url_resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="URL Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        text_resource = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Some text content",
            title="Text Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([url_resource, text_resource])
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/test-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 2

        # Find the URL resource in response
        url_item = next(
            item for item in data["items"] if item["id"] == str(url_resource.id)
        )
        text_item = next(
            item for item in data["items"] if item["id"] == str(text_resource.id)
        )

        # URL resource should have url field populated
        assert url_item["url"] == "https://example.com"

        # Text resource should have url field as None
        assert text_item["url"] is None

    async def test_get_node_resources_unauthenticated(
        self, client: AsyncClient
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/graph/nodes/test-tag/resources")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_node_resources_partial_tag_match(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that partial tag matches are not returned (exact match required)."""
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="Resource",
            tags=["python-advanced"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()

        # Search for "python" should not match "python-advanced"
        response = await client.get(
            "/graph/nodes/python/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_get_node_resources_ordering(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that resources are ordered by created_at descending."""
        # Create resources with explicit ordering (newer first)
        resource1 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/1",
            title="Older Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource1)
        await db_session.commit()
        await db_session.refresh(resource1)

        resource2 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/2",
            title="Newer Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource2)
        await db_session.commit()
        await db_session.refresh(resource2)

        response = await client.get(
            "/graph/nodes/test-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 2
        # Newer resource should be first
        assert data["items"][0]["id"] == str(resource2.id)
        assert data["items"][0]["title"] == "Newer Resource"
        assert data["items"][1]["id"] == str(resource1.id)
        assert data["items"][1]["title"] == "Older Resource"
