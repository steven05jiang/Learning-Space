"""Task queue configuration and utilities."""

import logging
from typing import Any, Dict

from arq import create_pool
from arq.connections import RedisSettings
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class QueueSettings(BaseSettings):
    """Redis queue configuration."""

    model_config = ConfigDict(env_prefix="REDIS_")

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None


queue_settings = QueueSettings()
redis_settings = RedisSettings(
    host=queue_settings.redis_host,
    port=queue_settings.redis_port,
    database=queue_settings.redis_db,
    password=queue_settings.redis_password,
)


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
        job = await pool.enqueue_job(job_name, *args, **kwargs)
        return job.job_id
    finally:
        pool.close()
        await pool.wait_closed()


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
        pool.close()
        await pool.wait_closed()


# Configure logging for job failures
logger = logging.getLogger(__name__)
