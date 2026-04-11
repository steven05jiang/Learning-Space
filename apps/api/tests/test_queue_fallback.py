"""Tests for queue fallback functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.queue import enqueue_job, get_job_status


class TestEnqueueJob:
    """Test enqueue_job with Redis fallback."""

    @pytest.mark.asyncio
    async def test_redis_success_returns_job_id(self):
        """Test successful Redis enqueue returns job_id."""
        mock_pool = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "redis-job-123"
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
        mock_pool.aclose = AsyncMock()

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            job_id = await enqueue_job("process_resource", "resource-1")

            assert job_id == "redis-job-123"
            mock_pool.enqueue_job.assert_called_once()
            mock_pool.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_failure_fallback_to_dispatch(self):
        """Test that Redis failure triggers fallback to direct dispatch."""
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(
            side_effect=ConnectionError("Redis unavailable")
        )
        mock_pool.aclose = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "fallback-job-456",
            "status": "queued",
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            with patch("core.queue.httpx.AsyncClient", return_value=mock_client):
                job_id = await enqueue_job("process_resource", "resource-1")

                assert job_id == "fallback-job-456"
                mock_pool.enqueue_job.assert_called_once()
                mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_redis_and_dispatch_fail(self):
        """Test error when both Redis and dispatch fail."""
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(
            side_effect=ConnectionError("Redis unavailable")
        )
        mock_pool.aclose = AsyncMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("Dispatch failed"))

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            with patch("core.queue.httpx.AsyncClient", return_value=mock_client):
                with pytest.raises(ConnectionError) as exc_info:
                    await enqueue_job("process_resource", "resource-1")

                assert "Both Redis and worker dispatch failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dispatch_connect_error(self):
        """Test error when dispatch endpoint is unreachable."""
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(
            side_effect=ConnectionError("Redis unavailable")
        )
        mock_pool.aclose = AsyncMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            with patch("core.queue.httpx.AsyncClient", return_value=mock_client):
                with pytest.raises(ConnectionError) as exc_info:
                    await enqueue_job("process_resource", "resource-1")

                assert "Both Redis and worker dispatch are unavailable" in str(
                    exc_info.value
                )

    @pytest.mark.asyncio
    async def test_dispatch_returns_error_status(self):
        """Test error when dispatch returns non-200 status."""
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(
            side_effect=ConnectionError("Redis unavailable")
        )
        mock_pool.aclose = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            with patch("core.queue.httpx.AsyncClient", return_value=mock_client):
                with pytest.raises(ConnectionError) as exc_info:
                    await enqueue_job("process_resource", "resource-1")

                assert "Worker dispatch failed with status 500" in str(exc_info.value)


class TestGetJobStatus:
    """Test get_job_status functionality."""

    @pytest.mark.asyncio
    async def test_get_existing_job(self):
        """Test getting status of an existing job."""
        mock_pool = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        mock_job.status.name = "completed"
        mock_job.result = {"success": True}
        mock_job.enqueue_time = "2026-04-10T00:00:00Z"
        mock_job.start_time = "2026-04-10T00:01:00Z"
        mock_job.finish_time = "2026-04-10T00:02:00Z"
        mock_pool.get_job = AsyncMock(return_value=mock_job)
        mock_pool.aclose = AsyncMock()

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            status = await get_job_status("job-123")

            assert status is not None
            assert status["id"] == "job-123"
            assert status["status"] == "completed"
            assert status["result"] == {"success": True}

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self):
        """Test getting status of a non-existent job."""
        mock_pool = AsyncMock()
        mock_pool.get_job = AsyncMock(return_value=None)
        mock_pool.aclose = AsyncMock()

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            status = await get_job_status("nonexistent")

            assert status is None

    @pytest.mark.asyncio
    async def test_get_job_redis_error(self):
        """Test graceful handling when Redis errors during status check."""
        mock_pool = AsyncMock()
        mock_pool.get_job = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
        mock_pool.aclose = AsyncMock()

        with patch("core.queue.create_queue_pool", return_value=mock_pool):
            status = await get_job_status("job-123")

            assert status is None  # Should return None, not raise
