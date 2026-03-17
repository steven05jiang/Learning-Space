"""Tests for task queue functionality."""

from unittest.mock import Mock, patch

import pytest

from services.queue_service import QueueService
from workers.tasks import job_failed, process_resource, sync_graph


class TestTaskFunctions:
    """Test task function implementations."""

    @pytest.mark.asyncio
    async def test_process_resource_success(self):
        """Test successful resource processing."""
        result = await process_resource("resource123", {"option1": "value1"})

        assert result["resource_id"] == "resource123"
        assert result["status"] == "processed"
        assert result["metadata"]["processing_options"] == {"option1": "value1"}
        assert "extraction" in result["metadata"]["stages_completed"]
        assert "analysis" in result["metadata"]["stages_completed"]

    @pytest.mark.asyncio
    async def test_process_resource_empty_id(self):
        """Test process_resource with empty resource_id."""
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            await process_resource("")

    @pytest.mark.asyncio
    async def test_process_resource_none_id(self):
        """Test process_resource with None resource_id."""
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            await process_resource(None)

    @pytest.mark.asyncio
    async def test_sync_graph_success(self):
        """Test successful graph synchronization."""
        result = await sync_graph("entity456", "update")

        assert result["entity_id"] == "entity456"
        assert result["operation"] == "update"
        assert result["status"] == "synced"
        assert result["graph_data"]["nodes_affected"] == 1

    @pytest.mark.asyncio
    async def test_sync_graph_all_operations(self):
        """Test sync_graph with all valid operations."""
        operations = ["create", "update", "delete"]

        for operation in operations:
            result = await sync_graph("entity123", operation)
            assert result["operation"] == operation
            assert result["status"] == "synced"

    @pytest.mark.asyncio
    async def test_sync_graph_invalid_operation(self):
        """Test sync_graph with invalid operation."""
        with pytest.raises(ValueError, match="operation must be one of"):
            await sync_graph("entity123", "invalid_op")

    @pytest.mark.asyncio
    async def test_sync_graph_empty_entity_id(self):
        """Test sync_graph with empty entity_id."""
        with pytest.raises(ValueError, match="entity_id cannot be empty"):
            await sync_graph("", "update")

    @pytest.mark.asyncio
    async def test_job_failed_handler(self):
        """Test job failure handler logs correctly."""
        mock_ctx = Mock()
        exception = ValueError("Test error")

        with patch("workers.tasks.logger") as mock_logger:
            await job_failed(mock_ctx, "job123", exception)
            mock_logger.error.assert_called_once()
            args = mock_logger.error.call_args[0]
            assert "job123" in args[0]
            assert "ValueError" in args[0]
            assert "Test error" in args[0]


class TestQueueService:
    """Test QueueService functionality."""

    @pytest.mark.asyncio
    async def test_enqueue_resource_processing_success(self):
        """Test successful resource processing job enqueueing."""
        with patch("services.queue_service.enqueue_job") as mock_enqueue:
            mock_enqueue.return_value = "job123"

            job_id = await QueueService.enqueue_resource_processing(
                "resource123", {"option": "value"}
            )

            assert job_id == "job123"
            mock_enqueue.assert_called_once_with(
                "process_resource", "resource123", {"option": "value"}
            )

    @pytest.mark.asyncio
    async def test_enqueue_resource_processing_empty_id(self):
        """Test resource processing with empty resource_id."""
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            await QueueService.enqueue_resource_processing("")

    @pytest.mark.asyncio
    async def test_enqueue_graph_sync_success(self):
        """Test successful graph sync job enqueueing."""
        with patch("services.queue_service.enqueue_job") as mock_enqueue:
            mock_enqueue.return_value = "job456"

            job_id = await QueueService.enqueue_graph_sync("entity123", "create")

            assert job_id == "job456"
            mock_enqueue.assert_called_once_with("sync_graph", "entity123", "create")

    @pytest.mark.asyncio
    async def test_enqueue_graph_sync_invalid_operation(self):
        """Test graph sync with invalid operation."""
        with pytest.raises(ValueError, match="operation must be one of"):
            await QueueService.enqueue_graph_sync("entity123", "invalid")

    @pytest.mark.asyncio
    async def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        mock_status = {
            "id": "job123",
            "status": "completed",
            "result": {"success": True},
            "enqueue_time": "2026-03-17T00:00:00Z",
            "start_time": "2026-03-17T00:01:00Z",
            "finish_time": "2026-03-17T00:02:00Z",
        }

        with patch("services.queue_service.get_job_status") as mock_get_status:
            mock_get_status.return_value = mock_status

            status = await QueueService.get_job_status("job123")

            assert status == mock_status
            mock_get_status.assert_called_once_with("job123")

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test job status when job not found."""
        with patch("services.queue_service.get_job_status") as mock_get_status:
            mock_get_status.return_value = None

            status = await QueueService.get_job_status("nonexistent")

            assert status is None


@pytest.mark.integration
class TestQueueIntegration:
    """Integration tests for queue functionality (requires Redis)."""

    @pytest.mark.asyncio
    async def test_queue_roundtrip(self):
        """Test enqueueing and status checking (requires running Redis)."""
        # This test would require actual Redis connection
        # For now, we'll skip it in regular test runs
        pytest.skip("Integration test - requires Redis")

    @pytest.mark.asyncio
    async def test_worker_functionality(self):
        """Test worker can process jobs (requires running Redis)."""
        # This test would require actual Redis and worker process
        # For now, we'll skip it in regular test runs
        pytest.skip("Integration test - requires Redis and worker")
