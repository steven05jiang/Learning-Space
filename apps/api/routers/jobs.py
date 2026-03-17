"""Job queue API endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.deps import get_current_user
from models.user import User
from services.queue_service import queue_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


class ResourceProcessingRequest(BaseModel):
    """Request model for resource processing jobs."""

    resource_id: str
    options: Dict[str, Any] | None = None


class GraphSyncRequest(BaseModel):
    """Request model for graph sync jobs."""

    entity_id: str
    operation: str = "update"


class JobResponse(BaseModel):
    """Response model for job operations."""

    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    id: str | None = None
    status: str | None = None
    result: Any | None = None
    enqueue_time: str | None = None
    start_time: str | None = None
    finish_time: str | None = None


@router.post("/process-resource", response_model=JobResponse)
async def enqueue_resource_processing(
    request: ResourceProcessingRequest,
    current_user: User = Depends(get_current_user),
):
    """Enqueue a resource processing job.

    Args:
        request: Resource processing request data

    Returns:
        Job ID and confirmation message

    Raises:
        HTTPException: If job enqueueing fails
    """
    try:
        job_id = await queue_service.enqueue_resource_processing(
            request.resource_id, request.options
        )
        message = f"Resource processing job enqueued for resource {request.resource_id}"
        return JobResponse(job_id=job_id, message=message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enqueue resource processing job: {e}")
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@router.post("/sync-graph", response_model=JobResponse)
async def enqueue_graph_sync(
    request: GraphSyncRequest,
    current_user: User = Depends(get_current_user),
):
    """Enqueue a graph synchronization job.

    Args:
        request: Graph sync request data

    Returns:
        Job ID and confirmation message

    Raises:
        HTTPException: If job enqueueing fails
    """
    try:
        job_id = await queue_service.enqueue_graph_sync(
            request.entity_id, request.operation
        )
        return JobResponse(
            job_id=job_id,
            message=f"Graph sync job enqueued for entity {request.entity_id}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enqueue graph sync job: {e}")
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the status of a job.

    Args:
        job_id: The job ID to check

    Returns:
        Job status information

    Raises:
        HTTPException: If job not found
    """
    try:
        status = await queue_service.get_job_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")
