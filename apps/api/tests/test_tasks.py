"""Tests for worker tasks."""

from unittest.mock import AsyncMock, patch

import pytest

from workers.tasks import sync_graph


class TestSyncGraph:
    """Test cases for sync_graph task."""

    @pytest.mark.asyncio
    async def test_sync_graph_delete_with_tags(self):
        """Test sync_graph with delete operation calls graph service methods."""
        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.remove_resource_tags = AsyncMock()
            mock_graph_service.cleanup_orphan_tags = AsyncMock()

            result = await sync_graph(
                entity_id="123", operation="delete", owner_id=1, tags=["AI", "Python"]
            )

            # Verify graph service methods were called
            mock_graph_service.remove_resource_tags.assert_called_once_with(
                1, ["AI", "Python"]
            )
            mock_graph_service.cleanup_orphan_tags.assert_called_once_with(1)

            # Verify result
            assert result == {
                "entity_id": "123",
                "operation": "delete",
                "status": "synced",
            }

    @pytest.mark.asyncio
    async def test_sync_graph_delete_without_tags(self):
        """Test sync_graph with delete operation but no tags returns noop."""
        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.remove_resource_tags = AsyncMock()
            mock_graph_service.cleanup_orphan_tags = AsyncMock()

            result = await sync_graph(
                entity_id="123", operation="delete", owner_id=1, tags=[]
            )

            # Verify graph service methods were NOT called
            mock_graph_service.remove_resource_tags.assert_not_called()
            mock_graph_service.cleanup_orphan_tags.assert_not_called()

            # Verify result
            assert result == {
                "entity_id": "123",
                "operation": "delete",
                "status": "noop",
            }

    @pytest.mark.asyncio
    async def test_sync_graph_delete_without_owner_id(self):
        """Test sync_graph with delete operation but no owner_id returns noop."""
        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.remove_resource_tags = AsyncMock()
            mock_graph_service.cleanup_orphan_tags = AsyncMock()

            result = await sync_graph(
                entity_id="123",
                operation="delete",
                owner_id=None,
                tags=["AI", "Python"],
            )

            # Verify graph service methods were NOT called
            mock_graph_service.remove_resource_tags.assert_not_called()
            mock_graph_service.cleanup_orphan_tags.assert_not_called()

            # Verify result
            assert result == {
                "entity_id": "123",
                "operation": "delete",
                "status": "noop",
            }

    @pytest.mark.asyncio
    async def test_sync_graph_create_operation(self):
        """Test sync_graph with create operation returns noop."""
        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.remove_resource_tags = AsyncMock()
            mock_graph_service.cleanup_orphan_tags = AsyncMock()

            result = await sync_graph(
                entity_id="123", operation="create", owner_id=1, tags=["AI", "Python"]
            )

            # Verify graph service methods were NOT called
            mock_graph_service.remove_resource_tags.assert_not_called()
            mock_graph_service.cleanup_orphan_tags.assert_not_called()

            # Verify result
            assert result == {
                "entity_id": "123",
                "operation": "create",
                "status": "noop",
            }

    @pytest.mark.asyncio
    async def test_sync_graph_update_operation(self):
        """Test sync_graph with update operation returns noop."""
        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.remove_resource_tags = AsyncMock()
            mock_graph_service.cleanup_orphan_tags = AsyncMock()

            result = await sync_graph(
                entity_id="123", operation="update", owner_id=1, tags=["AI", "Python"]
            )

            # Verify graph service methods were NOT called
            mock_graph_service.remove_resource_tags.assert_not_called()
            mock_graph_service.cleanup_orphan_tags.assert_not_called()

            # Verify result
            assert result == {
                "entity_id": "123",
                "operation": "update",
                "status": "noop",
            }

    @pytest.mark.asyncio
    async def test_sync_graph_empty_entity_id(self):
        """Test sync_graph with empty entity_id raises ValueError."""
        with pytest.raises(ValueError, match="entity_id cannot be empty"):
            await sync_graph(entity_id="")

    @pytest.mark.asyncio
    async def test_sync_graph_invalid_operation(self):
        """Test sync_graph with invalid operation raises ValueError."""
        with pytest.raises(ValueError, match="operation must be one of"):
            await sync_graph(entity_id="123", operation="invalid")
