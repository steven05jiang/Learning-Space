"""Resource management endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.resource import ResourceCreate, ResourceResponse, ResourceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])


async def process_resource_background_job(resource_id: int) -> None:
    """
    Placeholder background job for resource processing.

    This will be replaced with proper task queue integration in DEV-019.
    For now, just log the job dispatch.
    """
    logger.info(f"Background job enqueued for resource {resource_id}")


@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceResponse:
    """
    Create a new resource for processing.

    - **content_type**: Type of content ('url' or 'text')
    - **original_content**: The URL or text content to process
    - **prefer_provider**: Optional hint for processing provider

    Returns HTTP 202 with the resource data and status PENDING.
    A background job is enqueued for processing the resource.
    """
    # Create the resource in the database
    resource = Resource(
        owner_id=current_user.id,
        content_type=resource_data.content_type.value,
        original_content=resource_data.original_content,
        prefer_provider=resource_data.prefer_provider,
        status=ResourceStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(resource)
    await db.commit()
    await db.refresh(resource)

    # Enqueue background processing job
    background_tasks.add_task(process_resource_background_job, resource.id)

    logger.info(
        f"Created resource {resource.id} for user {current_user.id} "
        f"with content_type {resource_data.content_type.value}"
    )

    # Return the resource response
    return ResourceResponse(
        id=str(resource.id),
        owner_id=str(resource.owner_id),
        content_type=resource_data.content_type,
        original_content=resource.original_content,
        prefer_provider=resource.prefer_provider,
        title=resource.title,
        summary=resource.summary,
        tags=resource.tags or [],
        status=ResourceStatus(resource.status.value),
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )
