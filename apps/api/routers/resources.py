"""Resource management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.database import get_db
from models.resource import Resource
from models.resource import ResourceStatus as ModelResourceStatus
from models.user import User
from schemas.resource import (
    ContentType,
    ResourceCreate,
    ResourceListItem,
    ResourceListResponse,
    ResourceResponse,
    ResourceStatus,
)

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
    from datetime import datetime, timezone

    resource = Resource(
        owner_id=current_user.id,
        content_type=resource_data.content_type.value,
        original_content=resource_data.original_content,
        prefer_provider=resource_data.prefer_provider,
        status=ResourceStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
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


@router.get("/", response_model=ResourceListResponse)
async def list_resources(
    status_filter: Optional[ResourceStatus] = Query(
        None, alias="status", description="Filter by resource status"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceListResponse:
    """
    List resources owned by the authenticated user.

    - **status**: Optional filter by resource status
      (PENDING, PROCESSING, READY, FAILED)
    - **limit**: Maximum number of items to return (1-100, default 20)
    - **offset**: Number of items to skip for pagination (default 0)

    Returns a paginated list of resources with basic information.
    """
    # Build the base query
    query = select(Resource).where(Resource.owner_id == current_user.id)

    # Apply status filter if provided
    if status_filter:
        query = query.where(Resource.status == ModelResourceStatus(status_filter.value))

    # Add ordering by created_at descending (newest first)
    query = query.order_by(Resource.created_at.desc())

    # Get total count for pagination
    count_query = select(func.count(Resource.id)).where(
        Resource.owner_id == current_user.id
    )
    if status_filter:
        count_query = count_query.where(
            Resource.status == ModelResourceStatus(status_filter.value)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    paginated_query = query.offset(offset).limit(limit)

    # Execute the query
    result = await db.execute(paginated_query)
    resources = result.scalars().all()

    # Convert to response items
    items = []
    for resource in resources:
        # Set url field if content_type is URL
        url = (
            resource.original_content
            if resource.content_type == ContentType.URL.value
            else None
        )

        item = ResourceListItem(
            id=str(resource.id),
            url=url,
            title=resource.title,
            summary=resource.summary,
            tags=resource.tags or [],
            status=ResourceStatus(resource.status.value),
            created_at=resource.created_at,
        )
        items.append(item)

    logger.info(
        f"Listed {len(items)} resources for user {current_user.id} "
        f"(total: {total}, offset: {offset}, limit: {limit}, "
        f"status_filter: {status_filter})"
    )

    return ResourceListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
