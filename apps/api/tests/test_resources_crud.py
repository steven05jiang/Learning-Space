"""Tests for resource CRUD endpoints (GET, PATCH, DELETE /resources/{id})."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus
from models.user import User


@pytest.fixture
async def test_user_2(db_session: AsyncSession) -> User:
    """Create a second test user in the database."""
    user = User(
        email="test2@example.com",
        display_name="Test User 2",
        avatar_url="https://example.com/avatar2.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetResource:
    """Test cases for GET /resources/{id}."""

    @pytest.mark.asyncio
    async def test_get_resource_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test getting a resource successfully."""
        # Create a resource directly in the database
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/test",
            title="Test Resource",
            summary="A test resource for testing",
            tags=["test", "example"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Get the resource
        response = await client.get(f"/resources/{resource.id}", headers=auth_headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(resource.id)
        assert data["owner_id"] == str(test_user.id)
        assert data["content_type"] == "url"
        assert data["original_content"] == "https://example.com/test"
        assert data["title"] == "Test Resource"
        assert data["summary"] == "A test resource for testing"
        assert data["tags"] == ["test", "example"]
        assert data["status"] == "READY"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_resource_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting a non-existent resource returns 404."""
        response = await client.get("/resources/99999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_get_resource_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user_2,
    ):
        """Test getting a resource owned by another user returns 404."""
        # Create a resource owned by another user
        resource = Resource(
            owner_id=test_user_2.id,
            content_type="text",
            original_content="This belongs to another user",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Try to get the resource with the first user's auth
        response = await client.get(f"/resources/{resource.id}", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_get_resource_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests return 401."""
        response = await client.get("/resources/1")
        assert response.status_code == 401


class TestUpdateResource:
    """Test cases for PATCH /resources/{id}."""

    @pytest.mark.asyncio
    async def test_update_resource_title(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test updating only the title."""
        # Create a resource
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/test",
            title="Original Title",
            summary="Original summary",
            tags=["original"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        original_updated_at = resource.updated_at

        # Update only the title
        update_data = {"title": "Updated Title"}
        response = await client.patch(
            f"/resources/{resource.id}", json=update_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Title"
        assert data["summary"] == "Original summary"  # Unchanged
        assert data["tags"] == ["original"]  # Unchanged
        assert data["original_content"] == "https://example.com/test"  # Unchanged
        assert data["status"] == "READY"  # Unchanged

        # Verify updated_at changed
        # Note: We can't easily compare exact times in tests, but we can verify
        # the field exists
        assert "updated_at" in data

        # Verify in database
        await db_session.refresh(resource)
        assert resource.title == "Updated Title"
        assert resource.summary == "Original summary"
        assert resource.tags == ["original"]
        assert resource.status == ResourceStatus.READY
        assert resource.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_resource_multiple_fields(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test updating multiple fields at once."""
        # Create a resource
        resource = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Original content",
            title="Original Title",
            summary="Original summary",
            tags=["original"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Update multiple fields
        update_data = {
            "title": "New Title",
            "summary": "New summary",
            "tags": ["new", "updated"],
        }
        response = await client.patch(
            f"/resources/{resource.id}", json=update_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "New Title"
        assert data["summary"] == "New summary"
        assert data["tags"] == ["new", "updated"]
        assert data["original_content"] == "Original content"  # Unchanged
        assert data["status"] == "READY"  # Unchanged

        # Verify in database
        await db_session.refresh(resource)
        assert resource.title == "New Title"
        assert resource.summary == "New summary"
        assert resource.tags == ["new", "updated"]
        assert resource.status == ResourceStatus.READY

    @pytest.mark.asyncio
    async def test_update_original_content_resets_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test that updating original_content resets status to PENDING."""
        # Create a resource with READY status
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/original",
            title="Test Resource",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Update original_content
        update_data = {"original_content": "https://example.com/updated"}
        response = await client.patch(
            f"/resources/{resource.id}", json=update_data, headers=auth_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["original_content"] == "https://example.com/updated"
        assert data["status"] == "PENDING"  # Should be reset

        # Verify in database
        await db_session.refresh(resource)
        assert resource.original_content == "https://example.com/updated"
        assert resource.status == ResourceStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_resource_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating a non-existent resource returns 404."""
        update_data = {"title": "New Title"}
        response = await client.patch(
            "/resources/99999", json=update_data, headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_update_resource_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user_2,
    ):
        """Test updating a resource owned by another user returns 404."""
        # Create a resource owned by another user
        resource = Resource(
            owner_id=test_user_2.id,
            content_type="text",
            original_content="This belongs to another user",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Try to update the resource
        update_data = {"title": "Malicious Update"}
        response = await client.patch(
            f"/resources/{resource.id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

        # Verify resource was not updated
        await db_session.refresh(resource)
        assert resource.title is None  # Should still be None

    @pytest.mark.asyncio
    async def test_update_resource_empty_body(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test updating with empty body (no changes)."""
        # Create a resource
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/test",
            title="Original Title",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Update with empty body
        response = await client.patch(
            f"/resources/{resource.id}", json={}, headers=auth_headers
        )

        # Should succeed but make no changes
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Original Title"
        assert data["status"] == "READY"

    @pytest.mark.asyncio
    async def test_update_resource_invalid_original_content(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test updating with invalid original_content."""
        # Create a resource
        resource = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Valid content",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Try to update with empty original_content
        update_data = {"original_content": ""}
        response = await client.patch(
            f"/resources/{resource.id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_resource_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests return 401."""
        update_data = {"title": "New Title"}
        response = await client.patch("/resources/1", json=update_data)
        assert response.status_code == 401


class TestDeleteResource:
    """Test cases for DELETE /resources/{id}."""

    @pytest.mark.asyncio
    async def test_delete_resource_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test deleting a resource successfully."""
        # Create a resource
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/to-delete",
            title="Resource to Delete",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        resource_id = resource.id

        # Delete the resource
        response = await client.delete(
            f"/resources/{resource_id}", headers=auth_headers
        )

        # Verify response
        assert response.status_code == 204
        assert response.text == ""  # No content

        # Verify resource is deleted from database
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        deleted_resource = result.scalar_one_or_none()
        assert deleted_resource is None

    @pytest.mark.asyncio
    async def test_delete_resource_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting a non-existent resource returns 404."""
        response = await client.delete("/resources/99999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_delete_resource_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user_2,
    ):
        """Test deleting a resource owned by another user returns 404."""
        # Create a resource owned by another user
        resource = Resource(
            owner_id=test_user_2.id,
            content_type="text",
            original_content="This belongs to another user",
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        # Try to delete the resource
        response = await client.delete(
            f"/resources/{resource.id}", headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"

        # Verify resource still exists
        await db_session.refresh(resource)
        assert resource is not None

    @pytest.mark.asyncio
    async def test_delete_resource_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests return 401."""
        response = await client.delete("/resources/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_resource_with_tags_enqueues_graph_sync(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test that deleting a resource with tags enqueues graph sync job."""
        # Create a resource with tags
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/tagged-resource",
            title="Tagged Resource",
            tags=["AI", "Python", "Machine Learning"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        resource_id = resource.id

        # Mock the queue service
        with patch(
            "routers.resources.queue_service.enqueue_graph_sync"
        ) as mock_enqueue:
            mock_enqueue.return_value = "job123"

            # Delete the resource
            response = await client.delete(
                f"/resources/{resource_id}", headers=auth_headers
            )

            # Verify response
            assert response.status_code == 204

            # Verify graph sync job was enqueued with correct parameters
            mock_enqueue.assert_called_once_with(
                str(resource_id),
                operation="delete",
                owner_id=test_user.id,
                tags=["AI", "Python", "Machine Learning"]
            )

        # Verify resource is deleted from database
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        deleted_resource = result.scalar_one_or_none()
        assert deleted_resource is None

    @pytest.mark.asyncio
    async def test_delete_resource_without_tags_no_graph_sync(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test that deleting a resource without tags doesn't enqueue graph sync."""
        # Create a resource without tags
        resource = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Content without tags",
            title="Untagged Resource",
            tags=None,
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        resource_id = resource.id

        # Mock the queue service
        with patch(
            "routers.resources.queue_service.enqueue_graph_sync"
        ) as mock_enqueue:
            # Delete the resource
            response = await client.delete(
                f"/resources/{resource_id}", headers=auth_headers
            )

            # Verify response
            assert response.status_code == 204

            # Verify graph sync job was NOT enqueued
            mock_enqueue.assert_not_called()

        # Verify resource is deleted from database
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        deleted_resource = result.scalar_one_or_none()
        assert deleted_resource is None

    @pytest.mark.asyncio
    async def test_delete_resource_graph_sync_failure_doesnt_affect_deletion(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user,
    ):
        """Test that graph sync failure doesn't prevent successful resource deletion."""
        # Create a resource with tags
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/sync-fail-test",
            title="Sync Fail Test",
            tags=["tag1", "tag2"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        resource_id = resource.id

        # Mock the queue service to raise an exception
        with patch(
            "routers.resources.queue_service.enqueue_graph_sync"
        ) as mock_enqueue:
            mock_enqueue.side_effect = Exception("Graph sync failed")

            # Delete the resource
            response = await client.delete(
                f"/resources/{resource_id}", headers=auth_headers
            )

            # Verify response is still successful despite graph sync failure
            assert response.status_code == 204

            # Verify graph sync job was attempted
            mock_enqueue.assert_called_once()

        # Verify resource is still deleted from database
        stmt = select(Resource).where(Resource.id == resource_id)
        result = await db_session.execute(stmt)
        deleted_resource = result.scalar_one_or_none()
        assert deleted_resource is None
