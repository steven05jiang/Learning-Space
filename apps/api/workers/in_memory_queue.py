"""In-memory job queue for worker fallback when Redis is unavailable."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QueuedJob:
    """Represents a job in the in-memory queue."""

    job_id: str
    function_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)


class InMemoryQueue:
    """Thread-safe asyncio queue for in-memory job processing.

    Used as fallback when Redis is unavailable. Jobs enqueued via
    the dispatch API are added here and processed by the worker.
    """

    def __init__(self):
        self._queue: asyncio.Queue[QueuedJob | None] = asyncio.Queue()
        self._results: dict[str, Any] = {}
        self._running = False
        logger.info("In-memory queue initialized")

    @property
    def running(self) -> bool:
        """Check if the queue is running."""
        return self._running

    def start(self) -> None:
        """Mark the queue as running."""
        self._running = True
        logger.info("In-memory queue started")

    def stop(self) -> None:
        """Mark the queue as stopped and add sentinel to unblock consumers."""
        self._running = False
        # Add sentinel to unblock any waiting consumers
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        logger.info("In-memory queue stopped")

    async def enqueue(
        self, job_id: str, function_name: str, args: tuple, kwargs: dict
    ) -> str:
        """Add a job to the queue.

        Args:
            job_id: Unique job identifier
            function_name: Name of the function to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The job_id
        """
        job = QueuedJob(
            job_id=job_id,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
        )
        await self._queue.put(job)
        logger.info(f"Enqueued job {job_id} ({function_name}) to in-memory queue")
        return job_id

    async def dequeue(self) -> QueuedJob | None:
        """Get the next job from the queue.

        Returns:
            QueuedJob or None if queue is stopped
        """
        if not self._running:
            return None

        try:
            job = await self._queue.get()
            if job is None:
                # Sentinel received, queue is stopping
                return None
            return job
        except Exception as e:
            logger.error("InMemoryQueue.dequeue error: %s", e)
            return None

    def task_done(self) -> None:
        """Mark a task as done (called after processing)."""
        self._queue.task_done()

    async def wait_empty(self) -> None:
        """Wait until all items in the queue are processed."""
        await self._queue.join()

    def get_results(self) -> dict[str, Any]:
        """Get all stored results."""
        return self._results.copy()

    def set_result(self, job_id: str, result: Any) -> None:
        """Store a job result."""
        self._results[job_id] = result

    def get_result(self, job_id: str) -> Any | None:
        """Get a specific job result."""
        return self._results.get(job_id)


# Global in-memory queue instance
in_memory_queue = InMemoryQueue()
