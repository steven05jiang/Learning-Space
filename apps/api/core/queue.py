"""Task queue configuration and utilities.

Supports dual-mode operation:
1. Primary: Redis queue via ARQ
2. Fallback: Direct dispatch to worker when Redis is unavailable
"""

import logging
import uuid
from typing import Any, Dict
from urllib.parse import urlparse

import httpx
from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings

QUEUE_NAME = "learning_space_queue"

# Worker dispatch URL for fallback mode - constructed from settings.worker_url
WORKER_DISPATCH_URL = f"{settings.worker_url}/dispatch"

# Timeout for dispatch API calls
DISPATCH_TIMEOUT = 30.0


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

    Tries Redis first, falls back to direct worker dispatch if Redis fails.

    Args:
        job_name: Name of the job function to execute
        *args: Positional arguments for the job
        **kwargs: Keyword arguments for the job

    Returns:
        Job ID as string

    Raises:
        ConnectionError: If both Redis and fallback dispatch fail
        ValueError: If job_name is not valid
    """
    job_id = str(uuid.uuid4())
    redis_error_msg = None

    # Try Redis first (primary path)
    try:
        pool = await create_queue_pool()
        try:
            job = await pool.enqueue_job(
                job_name, *args, _queue_name=QUEUE_NAME, **kwargs
            )
            logger.debug(f"Job {job_id} enqueued to Redis")
            return job.job_id
        finally:
            await pool.aclose()
    except Exception as e:
        redis_error_msg = str(e)
        logger.warning(f"Redis enqueue failed for job {job_id}, trying fallback: {e}")

    # Fallback: direct dispatch to worker
    try:
        async with httpx.AsyncClient(timeout=DISPATCH_TIMEOUT) as client:
            response = await client.post(
                WORKER_DISPATCH_URL,
                json={
                    "job_id": job_id,
                    "function_name": job_name,
                    "args": list(args),
                    "kwargs": kwargs,
                },
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Job {job_id} dispatched via fallback to worker")
                return result.get("job_id", job_id)
            else:
                raise ConnectionError(
                    f"Worker dispatch failed with status "
                    f"{response.status_code}: {response.text}"
                )
    except httpx.ConnectError as e:
        logger.error(f"Worker dispatch endpoint unavailable: {e}")
        raise ConnectionError(
            "Both Redis and worker dispatch are unavailable. "
            f"Redis error: {redis_error_msg}, Dispatch error: {e}"
        )
    except Exception as dispatch_error:
        logger.error(f"Worker dispatch failed: {dispatch_error}")
        raise ConnectionError(
            "Both Redis and worker dispatch failed. "
            f"Redis error: {redis_error_msg}, "
            f"Dispatch error: {dispatch_error}"
        )


async def get_job_status(job_id: str) -> Dict[str, Any] | None:
    """Get job status and result.

    Note: Jobs dispatched via fallback (in-memory queue) don't have
    persistent status tracking. This function only works for Redis-queued jobs.

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
    except Exception as e:
        logger.warning(f"Failed to get job status for {job_id}: {e}")
        return None
    finally:
        await pool.aclose()


# Configure logging for job failures
logger = logging.getLogger(__name__)
