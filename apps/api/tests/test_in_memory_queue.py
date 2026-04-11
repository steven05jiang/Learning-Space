"""Tests for in-memory queue functionality."""

import asyncio

import pytest

from workers.in_memory_queue import InMemoryQueue, QueuedJob


class TestInMemoryQueue:
    """Test InMemoryQueue functionality."""

    @pytest.fixture
    def queue(self):
        """Create a fresh InMemoryQueue for each test."""
        return InMemoryQueue()

    @pytest.mark.asyncio
    async def test_enqueue_dequeue_basic(self, queue):
        """Test basic enqueue and dequeue operations."""
        queue.start()

        job_id = "test-job-1"
        await queue.enqueue(job_id, "process_resource", ("res1",), {"key": "value"})

        job = await queue.dequeue()
        assert job is not None
        assert job.job_id == job_id
        assert job.function_name == "process_resource"
        assert job.args == ("res1",)
        assert job.kwargs == {"key": "value"}

        queue.task_done()
        queue.stop()

    @pytest.mark.asyncio
    async def test_multiple_jobs(self, queue):
        """Test handling multiple jobs in sequence."""
        queue.start()

        for i in range(5):
            await queue.enqueue(f"job-{i}", "sync_graph", (f"entity{i}",), {})

        for i in range(5):
            job = await queue.dequeue()
            assert job is not None
            assert job.job_id == f"job-{i}"
            queue.task_done()

        queue.stop()

    @pytest.mark.asyncio
    async def test_dequeue_timeout_returns_none(self, queue):
        """Test that dequeue returns None on timeout when queue is empty."""
        queue.start()

        # Should timeout and return None after brief wait
        job = await queue.dequeue()
        assert job is None

        queue.stop()

    @pytest.mark.asyncio
    async def test_stop_unblocks_dequeue(self, queue):
        """Test that stop() unblocks waiting dequeue calls."""
        queue.start()

        # Start dequeue in background - it should unblock when we stop
        async def try_dequeue():
            return await queue.dequeue()

        dequeue_task = asyncio.create_task(try_dequeue())
        await asyncio.sleep(0.1)  # Let it start waiting

        queue.stop()

        result = await dequeue_task
        assert result is None

    @pytest.mark.asyncio
    async def test_result_storage(self, queue):
        """Test storing and retrieving job results."""
        queue.start()

        await queue.enqueue("job-1", "process_resource", (), {})
        _ = await queue.dequeue()

        queue.set_result("job-1", {"status": "success"})
        assert queue.get_result("job-1") == {"status": "success"}

        queue.task_done()
        queue.stop()

    @pytest.mark.asyncio
    async def test_get_results_returns_copy(self, queue):
        """Test that get_results returns a copy, not the original."""
        queue.start()

        queue.set_result("job-1", {"data": "original"})
        results = queue.get_results()

        results["job-1"] = {"data": "modified"}
        assert queue.get_result("job-1") == {"data": "original"}

        queue.stop()

    @pytest.mark.asyncio
    async def test_empty_args_kwargs(self, queue):
        """Test enqueue with empty args and kwargs."""
        queue.start()

        await queue.enqueue("job-1", "sync_graph", (), {})
        job = await queue.dequeue()

        assert job.args == ()
        assert job.kwargs == {}

        queue.task_done()
        queue.stop()

    @pytest.mark.asyncio
    async def test_running_state(self, queue):
        """Test running state management."""
        assert not queue.running

        queue.start()
        assert queue.running

        queue.stop()
        assert not queue.running

    @pytest.mark.asyncio
    async def test_queued_job_dataclass(self):
        """Test QueuedJob dataclass."""
        job = QueuedJob(
            job_id="test-123",
            function_name="process_resource",
            args=("arg1", "arg2"),
            kwargs={"key": "value"},
        )

        assert job.job_id == "test-123"
        assert job.function_name == "process_resource"
        assert job.args == ("arg1", "arg2")
        assert job.kwargs == {"key": "value"}
