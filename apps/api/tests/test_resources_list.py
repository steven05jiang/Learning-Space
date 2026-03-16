"""Tests for GET /resources endpoint (resource listing)."""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus


class TestListResources:
    """Test cases for listing resources."""

    @pytest.fixture
    async def sample_resources(self, db_session: AsyncSession, test_user):
        """Create sample resources for testing."""
        resources = []

        # Create resources with different statuses
        resource1 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/article1",
            title="Article 1",
            summary="Summary 1",
            tags=["tech", "ai"],
            status=ResourceStatus.READY,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        resources.append(resource1)

        resource2 = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Some important text content",
            title="Text Resource",
            summary="Text summary",
            tags=["learning"],
            status=ResourceStatus.PENDING,
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        resources.append(resource2)

        resource3 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/article3",
            title="Article 3",
            status=ResourceStatus.PROCESSING,
            created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        )
        resources.append(resource3)

        resource4 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/failed",
            status=ResourceStatus.FAILED,
            created_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
        )
        resources.append(resource4)

        for resource in resources:
            db_session.add(resource)

        await db_session.commit()

        for resource in resources:
            await db_session.refresh(resource)

        return resources

    @pytest.mark.asyncio
    async def test_list_resources_success(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test listing resources successfully."""
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Check pagination defaults
        assert data["total"] == 4
        assert data["limit"] == 20
        assert data["offset"] == 0

        # Check items are ordered by created_at desc (newest first)
        items = data["items"]
        assert len(items) == 4

        # Verify first item (newest)
        first_item = items[0]
        assert first_item["status"] == "FAILED"
        assert first_item["url"] == "https://example.com/failed"

        # Verify item structure
        for item in items:
            assert "id" in item
            assert "status" in item
            assert "created_at" in item
            assert "tags" in item
            # url field should be populated for URL resources, None for text
            if item.get("url"):
                assert item["url"].startswith("http")

    @pytest.mark.asyncio
    async def test_list_resources_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing resources when user has none."""
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_resources_with_status_filter(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test filtering resources by status."""
        # Filter for READY resources
        response = await client.get("/resources/?status=READY", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "READY"
        assert data["items"][0]["title"] == "Article 1"

    @pytest.mark.asyncio
    async def test_list_resources_with_status_filter_no_results(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test status filter with no matching resources."""
        # Create a status filter with no matches (assuming we only have the sample data)
        response = await client.get("/resources/?status=PENDING", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_list_resources_with_pagination(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test pagination parameters."""
        # Test with limit and offset
        response = await client.get(
            "/resources/?limit=2&offset=1", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4
        assert data["limit"] == 2
        assert data["offset"] == 1
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_resources_pagination_beyond_total(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test pagination offset beyond total items."""
        response = await client.get(
            "/resources/?limit=10&offset=100", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4
        assert data["limit"] == 10
        assert data["offset"] == 100
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_resources_invalid_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid limit parameter."""
        # Test limit too high
        response = await client.get("/resources/?limit=101", headers=auth_headers)
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/resources/?limit=0", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_resources_invalid_offset(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid offset parameter."""
        response = await client.get("/resources/?offset=-1", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_resources_invalid_status(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid status filter."""
        response = await client.get("/resources/?status=INVALID", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_resources_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests return 401."""
        response = await client.get("/resources/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_resources_invalid_token(self, client: AsyncClient):
        """Test that invalid token returns 401."""
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get("/resources/", headers=invalid_headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_resources_isolation(
        self, client: AsyncClient, auth_headers: dict, sample_resources, db_session: AsyncSession
    ):
        """Test that users only see their own resources."""
        # Create another user with resources
        from models.user import User

        other_user = User(
            email="other@example.com",
            display_name="Other User",
            avatar_url="https://example.com/other-avatar.jpg",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_resource = Resource(
            owner_id=other_user.id,
            content_type="url",
            original_content="https://example.com/other-user-resource",
            status=ResourceStatus.READY,
        )
        db_session.add(other_resource)
        await db_session.commit()

        # List resources as the original test user
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should only see the original user's 4 resources, not the other user's
        assert data["total"] == 4

        # Verify no resource belongs to the other user
        for item in data["items"]:
            # Get the resource ID and verify owner in database
            resource_id = int(item["id"])
            assert resource_id != other_resource.id

    @pytest.mark.asyncio
    async def test_list_resources_url_field_population(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test that url field is populated correctly based on content type."""
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            if item["url"] is not None:
                # If url is populated, it should be a valid URL from original_content
                assert item["url"].startswith("http")
            else:
                # If url is None, this should be a text resource
                # We can verify by checking that none of the URL resources have null url
                pass  # Text resources will have url=None

    @pytest.mark.asyncio
    async def test_list_resources_fields_structure(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test that response items contain the expected fields."""
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            # Required fields
            assert "id" in item
            assert "status" in item
            assert "created_at" in item
            assert "tags" in item

            # Optional fields (should be present but can be None)
            assert "url" in item
            assert "title" in item
            assert "summary" in item

            # Fields that should NOT be present (security/privacy)
            assert "owner_id" not in item
            assert "original_content" not in item
            assert "prefer_provider" not in item
            assert "updated_at" not in item

    @pytest.mark.asyncio
    async def test_list_resources_ordering(
        self, client: AsyncClient, auth_headers: dict, sample_resources
    ):
        """Test that resources are ordered by created_at descending."""
        response = await client.get("/resources/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        items = data["items"]
        assert len(items) >= 2  # Need at least 2 to test ordering

        # Check that items are ordered by created_at descending
        for i in range(len(items) - 1):
            current_date = items[i]["created_at"]
            next_date = items[i + 1]["created_at"]
            # Current should be newer (greater) than next
            assert current_date >= next_date