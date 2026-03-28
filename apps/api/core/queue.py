"""Task queue configuration and utilities."""

import logging
from typing import Any, Dict
from urllib.parse import urlparse

from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings

QUEUE_NAME = "learning_space_queue"


def _build_redis_settings() -> RedisSettings:
    """Build RedisSettings from REDIS_URL (supports redis:// and rediss://)."""
    parsed = urlparse(settings.redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
        ssl=parsed.scheme == "rediss",
    )


redis_settings = _build_redis_settings()


async def create_queue_pool():
    """Create and return a Redis connection pool for enqueueing jobs."""
    return await create_pool(redis_settings)


async def enqueue_job(job_name: str, *args, **kwargs) -> str:
    """Enqueue a job for processing.

    Args:
        job_name: Name of the job function to execute
        *args: Positional arguments for the job
        **kwargs: Keyword arguments for the job

    Returns:
        Job ID as string

    Raises:
        ConnectionError: If unable to connect to Redis
        ValueError: If job_name is not valid
    """
    pool = await create_queue_pool()
    try:
        job = await pool.enqueue_job(job_name, *args, _queue_name=QUEUE_NAME, **kwargs)
        return job.job_id
    finally:
        await pool.aclose()


async def get_job_status(job_id: str) -> Dict[str, Any] | None:
    """Get job status and result.

    Args:
        job_id: The job ID to check

    Returns:
        Job info dictionary or None if job not found
    """
    pool = await create_queue_pool()
    try:
        job = await pool.get_job(job_id)
        if job is None:
            return None

        return {
            "id": job.job_id,
            "status": job.status.name,
            "result": job.result,
            "enqueue_time": job.enqueue_time,
            "start_time": job.start_time,
            "finish_time": job.finish_time,
        }
    finally:
        await pool.aclose()


# Configure logging for job failures
logger = logging.getLogger(__name__)
