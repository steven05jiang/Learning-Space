"""Queue service for enqueueing jobs from the API layer."""

import logging
from typing import Any, Dict

from core.queue import enqueue_job, get_job_status

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing job queue operations."""

    @staticmethod
    async def enqueue_resource_processing(
        resource_id: str, options: Dict[str, Any] | None = None
    ) -> str:
        """Enqueue a resource processing job.

        Args:
            resource_id: The ID of the resource to process
            options: Optional processing configuration

        Returns:
            Job ID as string

        Raises:
            ValueError: If resource_id is invalid
            ConnectionError: If unable to connect to queue
        """
        if not resource_id:
            raise ValueError("resource_id cannot be empty")

        logger.info(f"Enqueueing resource processing job for resource_id={resource_id}")

        job_id = await enqueue_job("process_resource", resource_id, options)
        logger.info(f"Resource processing job enqueued with ID: {job_id}")
        return job_id

    @staticmethod
    async def enqueue_graph_sync(entity_id: str, operation: str = "update") -> str:
        """Enqueue a graph synchronization job.

        Args:
            entity_id: The ID of the entity to sync
            operation: Type of sync operation ('create', 'update', 'delete')

        Returns:
            Job ID as string

        Raises:
            ValueError: If entity_id or operation is invalid
            ConnectionError: If unable to connect to queue
        """
        if not entity_id:
            raise ValueError("entity_id cannot be empty")

        valid_operations = {"create", "update", "delete"}
        if operation not in valid_operations:
            raise ValueError(f"operation must be one of {valid_operations}")

        logger.info(f"Enqueueing graph sync job for entity_id={entity_id}, operation={operation}")

        job_id = await enqueue_job("sync_graph", entity_id, operation)
        logger.info(f"Graph sync job enqueued with ID: {job_id}")
        return job_id

    @staticmethod
    async def get_job_status(job_id: str) -> Dict[str, Any] | None:
        """Get the status of a job.

        Args:
            job_id: The job ID to check

        Returns:
            Job status dictionary or None if not found
        """
        return await get_job_status(job_id)


# Create singleton instance
queue_service = QueueService()