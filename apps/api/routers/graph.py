"""Graph-related endpoints."""

import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.resource import ResourceNodeItem, ResourceNodeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/nodes/{node_id}/resources", response_model=ResourceNodeResponse)
async def get_node_resources(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceNodeResponse:
    """
    Get resources associated with a graph node (tag).

    - **node_id**: The tag name to search for in resource tags
    - **limit**: Maximum number of items to return (1-100, default 50)
    - **offset**: Number of items to skip for pagination (default 0)

    Returns resources where the tags JSONB column contains the given tag name,
    scoped to the authenticated user. Uses GIN index on tags for efficient querying.
    """
    # Validate node_id to prevent LIKE injection attacks
    if not re.match(r'^[\w\s-]+$', node_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="node_id contains invalid characters. Only alphanumeric characters, hyphens, underscores, and spaces are allowed."
        )

    # Query resources where tags contains the node_id (tag name)
    # Handle both PostgreSQL (production) and SQLite (testing) JSON queries
    if db.bind.dialect.name == "postgresql":
        # Use PostgreSQL JSONB containment operator @> for efficient GIN index usage
        tag_condition = Resource.tags.op("@>")([node_id])
    else:
        # For SQLite (and other databases), use JSON search
        # This searches for the tag value in the JSON array
        tag_condition = Resource.tags.op("LIKE")(f"%{json.dumps(node_id)}%")

    query = select(Resource).where(
        Resource.owner_id == current_user.id,
        tag_condition
    ).order_by(Resource.created_at.desc())

    # Get total count for pagination metadata
    count_query = select(func.count(Resource.id)).where(
        Resource.owner_id == current_user.id,
        tag_condition
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination to the main query
    paginated_query = query.offset(offset).limit(limit)

    # Execute the main query
    result = await db.execute(paginated_query)
    resources = result.scalars().all()

    # Convert to response items
    items = []
    for resource in resources:
        item = ResourceNodeItem(
            id=str(resource.id),
            title=resource.title,
            summary=resource.summary,
            original_content=resource.original_content,
            content_type=resource.content_type,
            status=resource.status.value,
            created_at=resource.created_at,
            tags=resource.tags or [],
        )
        items.append(item)

    logger.info(
        f"Retrieved {len(items)} resources for node '{node_id}' "
        f"for user {current_user.id} (total: {total}, limit: {limit}, offset: {offset})"
    )

    return ResourceNodeResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
