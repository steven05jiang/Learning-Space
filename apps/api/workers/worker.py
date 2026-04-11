"""ARQ worker configuration and startup.

Supports dual queue monitoring:
1. Redis queue (primary) via ARQ polling
2. In-memory queue (fallback) for direct dispatches
"""

import asyncio
import logging
import os
from multiprocessing import Process
from typing import Any, Dict

import uvicorn

from core.queue import QUEUE_NAME, redis_settings
from services.neo4j_driver import neo4j_driver
from workers.dispatch_api import dispatch_app

# Import in-memory queue
from workers.in_memory_queue import in_memory_queue
from workers.tasks import job_failed, process_resource, sync_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Function registry for dispatch API
FUNCTION_REGISTRY: Dict[str, callable] = {
    "process_resource": process_resource,
    "sync_graph": sync_graph,
}


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
    # Override with BURST_MODE=true env var
    burst = os.environ.get("BURST_MODE", "").lower() == "true"

    # Poll interval in seconds (default 30s to reduce Upstash commands)
    poll_delay = int(os.environ.get("REDIS_POLL_INTERVAL", 30))

    # Job failure handler
    on_job_failure = job_failed

    # Worker name for identification
    queue_name = QUEUE_NAME

    # Lifecycle hooks
    async def on_startup(ctx):
        await neo4j_driver.connect()

    async def on_shutdown(ctx):
        await neo4j_driver.disconnect()


async def process_in_memory_job(
    job_id: str, function_name: str, args: tuple, kwargs: dict
) -> Any:
    """Process a job from the in-memory queue.

    Args:
        job_id: Unique job identifier
        function_name: Name of the function to call
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Job result
    """
    logger.info(f"Processing in-memory job {job_id} ({function_name})")

    if function_name not in FUNCTION_REGISTRY:
        raise ValueError(f"Unknown function: {function_name}")

    func = FUNCTION_REGISTRY[function_name]
    ctx: Dict[str, Any] = {}

    try:
        result = await func(ctx, *args, **kwargs)
        in_memory_queue.set_result(job_id, result)
        logger.info(f"In-memory job {job_id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"In-memory job {job_id} failed: {e}")
        # Call job failure handler
        await job_failed(ctx, job_id, e)
        raise


async def in_memory_queue_worker() -> None:
    """Worker coroutine that processes jobs from the in-memory queue.

    This runs alongside the dispatch server and processes direct dispatches
    when Redis is unavailable.
    """
    logger.info("In-memory queue worker started")

    while in_memory_queue.running:
        try:
            job = await in_memory_queue.dequeue()

            if job is None:
                # Sentinel received, queue is stopping
                break

            try:
                await process_in_memory_job(
                    job.job_id,
                    job.function_name,
                    job.args,
                    job.kwargs,
                )
            except Exception as e:
                logger.error(f"Failed to process in-memory job {job.job_id}: {e}")
            finally:
                in_memory_queue.task_done()

        except asyncio.CancelledError:
            logger.info("In-memory queue worker cancelled")
            break
        except Exception as e:
            logger.error(f"Error in in-memory queue worker: {e}")
            await asyncio.sleep(1)  # Brief pause before retrying

    logger.info("In-memory queue worker stopped")


async def run_dispatch_server() -> None:
    """Run the dispatch API server."""
    config = uvicorn.Config(
        dispatch_app,
        host="127.0.0.1",
        port=int(os.environ.get("DISPATCH_PORT", "8001")),
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


def _run_arq_worker_subprocess() -> None:
    """Run ARQ worker in a subprocess (entry point for Process)."""
    import asyncio
    import logging
    import sys

    from arq import run_worker

    # Configure logging to reduce verbosity from ARQ/Redis libraries
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # Silence extremely verbose loggers
    logging.getLogger("arq.worker").setLevel(logging.WARNING)
    logging.getLogger("redis.asyncio").setLevel(logging.WARNING)
    logging.getLogger("redis.io_asyncio").setLevel(logging.WARNING)

    # Create event loop for subprocess main thread (Python 3.14+ requirement)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run ARQ worker - it manages its own event loop
        # Note: If Redis is unavailable, ARQ will keep retrying internally
        # and the subprocess stays alive. The in-memory queue handles
        # fallback dispatches independently.
        run_worker(WorkerSettings)
    except KeyboardInterrupt:
        pass  # Normal shutdown
    except Exception as e:
        # Log but don't propagate - let the subprocess exit gracefully
        logging.error("ARQ worker subprocess exiting: %s", e)
    finally:
        try:
            loop.close()
        except Exception:
            pass


async def start_dual_worker() -> None:
    """Start both the dispatch server and in-memory queue worker.

    The ARQ worker runs in a separate process to avoid event loop conflicts.
    The dispatch server and in-memory worker run in the main process.
    """
    # Start ARQ worker as a subprocess
    arq_process = Process(target=_run_arq_worker_subprocess, daemon=True)
    arq_process.start()
    logger.info(f"Started ARQ worker subprocess (pid={arq_process.pid})")

    # Start the in-memory queue (before creating the worker task)
    in_memory_queue.start()

    # Connect to Neo4j for in-memory queue worker
    await neo4j_driver.connect()

    # Start dispatch API server and in-memory queue worker as background tasks
    dispatch_task = asyncio.create_task(run_dispatch_server())
    in_memory_task = asyncio.create_task(in_memory_queue_worker())

    logger.info("Dual-mode worker started (Redis + in-memory queue)")

    def shutdown():
        """Cleanup function to stop all workers."""
        logger.info("Shutting down dual-mode worker...")
        in_memory_queue.stop()
        dispatch_task.cancel()
        in_memory_task.cancel()
        if arq_process.is_alive():
            arq_process.terminate()
            arq_process.join(timeout=5)
            if arq_process.is_alive():
                arq_process.kill()
        # Disconnect Neo4j
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(neo4j_driver.disconnect())
            else:
                loop.run_until_complete(neo4j_driver.disconnect())
        except Exception as e:
            logger.warning("Error disconnecting Neo4j: %s", e)
        logger.info("Dual-mode worker stopped")

    try:
        # Wait for both tasks
        await asyncio.gather(dispatch_task, in_memory_task, return_exceptions=True)
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
        shutdown()
    except Exception as e:
        logger.error(f"Error in dual-mode worker: {e}")
        shutdown()
        raise


if __name__ == "__main__":
    # Check if we should run in dual-mode
    if os.environ.get("DUAL_MODE", "").lower() == "true":
        logger.info("Starting in dual-mode (Redis + in-memory fallback)")
        asyncio.run(start_dual_worker())
    else:
        logger.info("Starting Learning Space task worker...")
        from arq import run_worker

        run_worker(WorkerSettings)
