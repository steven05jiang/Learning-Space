"""ARQ worker configuration and startup."""

import logging
from typing import Dict, Any

from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker

from core.queue import redis_settings
from workers.tasks import process_resource, sync_graph, job_failed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WorkerSettings:
    """ARQ worker configuration."""

    # Redis connection settings
    redis_settings = redis_settings

    # Job functions available to the worker
    functions = [process_resource, sync_graph]

    # Worker configuration
    max_jobs = 10
    job_timeout = 600  # 10 minutes
    keep_result = 3600  # Keep results for 1 hour
    max_tries = 3  # Retry failed jobs up to 3 times

    # Job failure handler
    on_job_failure = job_failed

    # Worker name for identification
    queue_name = "learning_space_queue"


async def main():
    """Start the ARQ worker."""
    logger.info("Starting Learning Space task worker...")

    # Create Redis pool
    redis_pool = await create_pool(redis_settings)

    # Create and run worker
    worker = Worker(
        functions=WorkerSettings.functions,
        redis_pool=redis_pool,
        max_jobs=WorkerSettings.max_jobs,
        job_timeout=WorkerSettings.job_timeout,
        keep_result=WorkerSettings.keep_result,
        max_tries=WorkerSettings.max_tries,
        on_job_failure=WorkerSettings.on_job_failure,
        queue_name=WorkerSettings.queue_name,
    )

    try:
        await worker.main()
    finally:
        await redis_pool.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())