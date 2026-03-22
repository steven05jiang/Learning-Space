"""ARQ worker configuration and startup."""

import logging

from arq import run_worker

from core.queue import QUEUE_NAME, redis_settings
from services.neo4j_driver import neo4j_driver
from workers.tasks import job_failed, process_resource, sync_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    queue_name = QUEUE_NAME

    # Lifecycle hooks
    async def on_startup(ctx):
        await neo4j_driver.connect()

    async def on_shutdown(ctx):
        await neo4j_driver.disconnect()


if __name__ == "__main__":
    logger.info("Starting Learning Space task worker...")
    run_worker(WorkerSettings)
