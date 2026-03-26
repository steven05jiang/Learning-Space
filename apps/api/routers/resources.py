"""Resource management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.database import get_db
from models.resource import ProcessingStatus as ModelProcessingStatus
from models.resource import Resource
from models.resource import ResourceStatus as ModelResourceStatus
from models.user import User
from schemas.resource import (
    ContentType,
    ProcessingStatus,
    ResourceCreate,
    ResourceListItem,
    ResourceListResponse,
    ResourceResponse,
    ResourceStatus,
    ResourceUpdate,
)
from services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])


async def process_resource_background_job(resource_id: int) -> None:
    """Enqueue resource for processing via the task queue."""
    try:
        job_id = await queue_service.enqueue_resource_processing(str(resource_id))
        logger.info(f"Resource {resource_id} enqueued for processing, job_id={job_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue resource {resource_id}: {e}")


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
    Returns HTTP 409 if the URL already exists for this user.
    """
    # Check for duplicate URLs (only for URL content type)
    if resource_data.content_type.value == "url":
        existing_query = select(Resource).where(
            Resource.owner_id == current_user.id,
            Resource.content_type == "url",
            Resource.original_content == resource_data.original_content,
        )
        existing_result = await db.execute(existing_query)
        existing_resource = existing_result.scalar_one_or_none()

        if existing_resource:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This resource has already been added.",
            )

    # Create the resource in the database
    resource = Resource(
        owner_id=current_user.id,
        content_type=resource_data.content_type.value,
        original_content=resource_data.original_content,
        prefer_provider=resource_data.prefer_provider,
        status=ResourceStatus.PENDING,
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
        processing_status=ProcessingStatus(resource.processing_status.value),
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
            processing_status=ProcessingStatus(resource.processing_status.value),
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


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceResponse:
    """
    Get a single resource by ID.

    - **resource_id**: The resource ID to retrieve

    Returns the full resource data if found and owned by the authenticated user.
    Returns 404 if the resource doesn't exist or is not owned by the user.
    """
    # Query for the resource, ensuring ownership
    query = select(Resource).where(
        Resource.id == resource_id, Resource.owner_id == current_user.id
    )
    result = await db.execute(query)
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    logger.info(f"Retrieved resource {resource_id} for user {current_user.id}")

    # Return the resource response
    return ResourceResponse(
        id=str(resource.id),
        owner_id=str(resource.owner_id),
        content_type=ContentType(resource.content_type),
        original_content=resource.original_content,
        prefer_provider=resource.prefer_provider,
        title=resource.title,
        summary=resource.summary,
        tags=resource.tags or [],
        status=ResourceStatus(resource.status.value),
        processing_status=ProcessingStatus(resource.processing_status.value),
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceResponse:
    """
    Update a resource (partial update).

    - **resource_id**: The resource ID to update
    - **title**: Optional new title
    - **summary**: Optional new summary
    - **tags**: Optional new tags list
    - **original_content**: Optional new content (triggers reprocessing)

    Only provided fields are updated (PATCH semantics).
    If original_content changes, status is reset to PENDING.
    Returns 404 if the resource doesn't exist or is not owned by the user.
    """
    # Query for the resource, ensuring ownership
    query = select(Resource).where(
        Resource.id == resource_id, Resource.owner_id == current_user.id
    )
    result = await db.execute(query)
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    # Get only the fields that were actually provided
    update_data = resource_data.model_dump(exclude_unset=True)

    # Check if original_content is being updated
    original_content_changed = "original_content" in update_data

    # Apply updates
    for field, value in update_data.items():
        setattr(resource, field, value)

    # If original_content changed, reset status to PENDING
    if original_content_changed:
        resource.status = ModelResourceStatus.PENDING
        # TODO: enqueue process_resource job (DEV-019)
        logger.info(
            f"Resource {resource_id} original_content updated, status reset to PENDING"
        )

    # Commit changes (updated_at is automatically updated by SQLAlchemy onupdate)
    await db.commit()
    await db.refresh(resource)

    logger.info(f"Updated resource {resource_id} for user {current_user.id}")

    # Return the updated resource response
    return ResourceResponse(
        id=str(resource.id),
        owner_id=str(resource.owner_id),
        content_type=ContentType(resource.content_type),
        original_content=resource.original_content,
        prefer_provider=resource.prefer_provider,
        title=resource.title,
        summary=resource.summary,
        tags=resource.tags or [],
        status=ResourceStatus(resource.status.value),
        processing_status=ProcessingStatus(resource.processing_status.value),
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@router.post("/{resource_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_resource(
    resource_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Reprocess an existing resource.

    - **resource_id**: The resource ID to reprocess

    Resets the processing_status to PENDING and enqueues a new processing job.
    This is useful for retrying failed resources or forcing re-summarization.
    Returns 202 on successful enqueueing.
    Returns 404 if the resource doesn't exist or is not owned by the user.
    """
    # Query for the resource, ensuring ownership
    query = select(Resource).where(
        Resource.id == resource_id, Resource.owner_id == current_user.id
    )
    result = await db.execute(query)
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    # Reset processing status to pending
    resource.processing_status = ModelProcessingStatus.PENDING
    await db.commit()
    await db.refresh(resource)

    # Enqueue background processing job
    background_tasks.add_task(process_resource_background_job, resource.id)

    logger.info(
        f"Resource {resource_id} marked for reprocessing by user {current_user.id}"
    )

    return {"message": "Resource queued for reprocessing"}


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a resource.

    - **resource_id**: The resource ID to delete

    Permanently removes the resource from the database.
    Returns 404 if the resource doesn't exist or is not owned by the user.
    """
    # Query for the resource, ensuring ownership
    query = select(Resource).where(
        Resource.id == resource_id, Resource.owner_id == current_user.id
    )
    result = await db.execute(query)
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    # Capture before delete
    owner_id = resource.owner_id
    tags = resource.tags or []

    # Delete the resource
    await db.delete(resource)
    await db.commit()

    # Enqueue graph sync (non-blocking — don't await the job result)
    if tags:
        try:
            await queue_service.enqueue_graph_sync(
                str(resource_id), operation="delete", owner_id=owner_id, tags=tags
            )
        except Exception as e:
            # Don't fail the delete response for graph sync errors
            logger.warning(
                f"Graph sync job enqueueing failed for deleted resource "
                f"{resource_id}: {e}"
            )

    logger.info(f"Deleted resource {resource_id} for user {current_user.id}")

    # Return 204 No Content (FastAPI automatically handles this with the status_code)
