"""FastAPI dispatch endpoint for direct task submission to worker.

This API runs alongside the ARQ worker and provides an alternative
pathway for job dispatch when Redis is unavailable.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from workers.in_memory_queue import in_memory_queue

logger = logging.getLogger(__name__)


class DispatchRequest(BaseModel):
    """Request model for task dispatch."""

    job_id: str
    function_name: str
    args: list[Any] = []
    kwargs: dict[str, Any] = {}


class DispatchResponse(BaseModel):
    """Response model for task dispatch."""

    job_id: str
    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    queue_running: bool
    queue_size: int


async def process_in_memory_job(
    job_id: str, function_name: str, args: tuple, kwargs: dict
):
    """Process a job from the in-memory queue.

    Args:
        job_id: Unique job identifier
        function_name: Name of the function to call
        args: Positional arguments
        kwargs: Keyword arguments
    """
    logger.info(f"Processing in-memory job {job_id} ({function_name})")

    from workers.tasks import job_failed, process_resource, sync_graph

    FUNCTION_REGISTRY = {
        "process_resource": process_resource,
        "sync_graph": sync_graph,
    }

    if function_name not in FUNCTION_REGISTRY:
        raise ValueError(f"Unknown function: {function_name}")

    func = FUNCTION_REGISTRY[function_name]
    ctx = {}

    try:
        result = await func(ctx, *args, **kwargs)
        in_memory_queue.set_result(job_id, result)
        logger.info(f"In-memory job {job_id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"In-memory job {job_id} failed: {e}")
        await job_failed(ctx, job_id, e)
        raise


async def in_memory_queue_worker() -> None:
    """Worker coroutine that processes jobs from the in-memory queue."""
    logger.info("In-memory queue worker started")

    while in_memory_queue.running:
        try:
            job = await in_memory_queue.dequeue()

            if job is None:
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
            await asyncio.sleep(1)

    logger.info("In-memory queue worker stopped")


def run_arq_subprocess():
    """Run ARQ worker in a subprocess (must be at module level for pickling)."""
    import asyncio
    import logging
    import sys

    from arq import run_worker

    from core.queue import QUEUE_NAME
    from core.queue import redis_settings as _redis_settings
    from services.neo4j_driver import neo4j_driver
    from workers.tasks import job_failed, process_resource, sync_graph

    class WorkerSettings:
        redis_settings = _redis_settings
        functions = [process_resource, sync_graph]
        max_jobs = 10
        job_timeout = 600
        keep_result = 3600
        max_tries = 3
        burst = False
        poll_delay = 30
        on_job_failure = job_failed
        queue_name = QUEUE_NAME

        async def on_startup(ctx):
            await neo4j_driver.connect()

        async def on_shutdown(ctx):
            await neo4j_driver.disconnect()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("arq.worker").setLevel(logging.WARNING)
    logging.getLogger("redis.asyncio").setLevel(logging.WARNING)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        run_worker(WorkerSettings)
    except KeyboardInterrupt:
        pass  # Normal shutdown
    except Exception as e:
        # Log but don't propagate - let the subprocess exit gracefully
        logging.error("ARQ worker subprocess exiting: %s", e)
    finally:
        try:
            loop.close()
        except Exception as exc:
            # Ignore errors during loop cleanup on shutdown
            logging.debug("Event loop close error (shutdown): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage dispatch API lifecycle."""
    from multiprocessing import Process

    from services.neo4j_driver import neo4j_driver

    # Connect to Neo4j for in-memory queue worker
    await neo4j_driver.connect()

    # Startup
    in_memory_queue.start()
    worker_task = asyncio.create_task(in_memory_queue_worker())
    # Start ARQ worker as subprocess
    arq_process = Process(target=run_arq_subprocess, daemon=True)
    arq_process.start()
    logger.info("Dispatch API starting with ARQ worker")

    yield

    # Shutdown
    worker_task.cancel()
    in_memory_queue.stop()
    if arq_process.is_alive():
        arq_process.terminate()
        arq_process.join(timeout=5)
        if arq_process.is_alive():
            arq_process.kill()
    # Disconnect Neo4j
    try:
        await neo4j_driver.disconnect()
    except Exception as e:
        logger.warning("Error disconnecting Neo4j: %s", e)
    logger.info("Dispatch API shutting down")


# FastAPI app for dispatch endpoint
dispatch_app = FastAPI(
    title="Worker Dispatch API",
    description="Internal API for direct task dispatch to worker",
    version="1.0.0",
    lifespan=lifespan,
)


@dispatch_app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check if the dispatch API and queue are healthy."""
    return HealthResponse(
        status="healthy",
        queue_running=in_memory_queue.running,
        queue_size=in_memory_queue._queue.qsize(),  # noqa: SLF001
    )


@dispatch_app.post("/dispatch", response_model=DispatchResponse)
async def dispatch_task(request: DispatchRequest) -> DispatchResponse:
    """Dispatch a task to the worker's in-memory queue.

    This endpoint is called by the API server when Redis is unavailable.
    The task is added to the in-memory queue and processed asynchronously.

    Args:
        request: Task dispatch request

    Returns:
        Dispatch response with job_id and status
    """
    try:
        # Validate function name
        valid_functions = {"process_resource", "sync_graph"}
        if request.function_name not in valid_functions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown function: {request.function_name}. "
                f"Valid functions: {valid_functions}",
            )

        # Enqueue to in-memory queue
        job_id = await in_memory_queue.enqueue(
            job_id=request.job_id,
            function_name=request.function_name,
            args=tuple(request.args),
            kwargs=request.kwargs,
        )

        logger.info(f"Dispatched job {job_id} ({request.function_name})")

        return DispatchResponse(
            job_id=job_id,
            status="queued",
            message=f"Task {request.function_name} queued for processing",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to dispatch task {request.job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch task: {str(e)}",
        )
