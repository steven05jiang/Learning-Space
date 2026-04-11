"""FastAPI dispatch endpoint for direct task submission to worker.

This API runs alongside the ARQ worker and provides an alternative
pathway for job dispatch when Redis is unavailable.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from core.config import settings
from workers.in_memory_queue import in_memory_queue

logger = logging.getLogger(__name__)

# Dispatch API configuration from settings
_parsed = urlparse(settings.worker_url)
DISPATCH_HOST = _parsed.hostname or "127.0.0.1"
DISPATCH_PORT = _parsed.port or 8001


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage dispatch API lifecycle."""
    # Startup
    in_memory_queue.start()
    logger.info(f"Dispatch API starting on {DISPATCH_HOST}:{DISPATCH_PORT}")
    yield
    # Shutdown
    in_memory_queue.stop()
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


async def run_dispatch_server() -> None:
    """Run the dispatch API server."""
    import uvicorn

    config = uvicorn.Config(
        dispatch_app,
        host=DISPATCH_HOST,
        port=DISPATCH_PORT,
        log_level="info",
        access_log=False,  # Reduce noise
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_dispatch_server())
