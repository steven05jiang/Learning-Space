"""Graph-related endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.resource import ResourceListItem, ResourceListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/nodes/{node_id}/resources", response_model=ResourceListResponse)
async def get_node_resources(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceListResponse:
    """
    Get resources associated with a graph node (tag).

    - **node_id**: The tag name to search for in resource tags

    Returns resources where the tags JSONB column contains the given tag name,
    scoped to the authenticated user. Uses GIN index on tags for efficient querying.
    """
    # Query resources where tags contains the node_id (tag name)
    # Handle both PostgreSQL (production) and SQLite (testing) JSON queries
    if db.bind.dialect.name == "postgresql":
        # Use PostgreSQL JSONB containment operator @> for efficient GIN index usage
        tag_condition = Resource.tags.op("@>")([node_id])
    else:
        # For SQLite (and other databases), use JSON search
        # This searches for the tag value in the JSON array
        import json
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

    # Execute the main query
    result = await db.execute(query)
    resources = result.scalars().all()

    # Convert to response items
    items = []
    for resource in resources:
        # Set url field if content_type is URL
        url = (
            resource.original_content
            if resource.content_type == "url"
            else None
        )

        item = ResourceListItem(
            id=str(resource.id),
            url=url,
            title=resource.title,
            summary=resource.summary,
            tags=resource.tags or [],
            status=resource.status.value,
            created_at=resource.created_at,
        )
        items.append(item)

    logger.info(
        f"Retrieved {len(items)} resources for node '{node_id}' "
        f"for user {current_user.id} (total: {total})"
    )

    return ResourceListResponse(
        items=items,
        total=total,
        limit=len(items),  # Return all matching resources for now
        offset=0,
    )