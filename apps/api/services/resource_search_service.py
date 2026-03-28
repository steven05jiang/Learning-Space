"""
Resource search service for full-text search capabilities.

This service provides unified search functionality for both HTTP endpoints and
AI agent tools, using PostgreSQL full-text search with tsvector and ts_rank.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import String, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# PostgreSQL full-text search expression for tsvector generation
TSVECTOR_EXPRESSION = """to_tsvector('english',
    COALESCE(title,'') || ' ' ||
    COALESCE(summary,'') || ' ' ||
    COALESCE(tags::text,'[]')
)"""


@dataclass
class ResourceSearchItem:
    """Internal model for search results containing all resource fields plus rank."""

    id: str
    title: Optional[str]
    summary: Optional[str]
    tags: List[str]
    top_level_categories: List[str]
    original_content: str
    content_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    rank: float

    @classmethod
    def from_row(cls, row) -> "ResourceSearchItem":
        """Create ResourceSearchItem from SQLAlchemy result row."""
        return cls(
            id=str(row.id),
            title=row.title,
            summary=row.summary,
            tags=row.tags or [],
            top_level_categories=row.top_level_categories or [],
            original_content=row.original_content,
            content_type=row.content_type,
            status=(
                row.status.value if hasattr(row.status, "value") else str(row.status)
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
            rank=float(row.rank),
        )


@dataclass
class SearchResult:
    """Container for search results with pagination support."""

    resources: List[ResourceSearchItem]
    total: int


@dataclass
class AgentResourceResult:
    """Trimmed resource result shape for AI agent consumption."""

    id: str
    title: str
    summary: str
    tags: List[str]
    top_level_categories: List[str]
    url: Optional[str]

    @classmethod
    def from_item(cls, item: ResourceSearchItem) -> "AgentResourceResult":
        """Convert ResourceSearchItem to AgentResourceResult for agent tools."""
        return cls(
            id=item.id,
            title=item.title or "",
            summary=item.summary or "",
            tags=item.tags,
            top_level_categories=item.top_level_categories,
            url=item.original_content if item.content_type == "url" else None,
        )


class ResourceSearchService:
    """Service for searching user resources with full-text search capabilities."""

    def __init__(self):
        pass

    async def search(
        self,
        session: AsyncSession,
        owner_id: UUID,
        query: str,
        tag: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResult:
        """
        Search the current user's resources.

        Args:
            session:   AsyncSession for database operations.
            owner_id:  The authenticated user's ID. Results are scoped to this user.
            query:     One or more keywords (natural language). Required and non-empty.
            tag:       Optional tag filter. Narrows results to resources with this tag.
            limit:     Max results to return. HTTP callers use default 20.
            offset:    Pagination offset. Agent callers always use 0.

        Returns:
            SearchResult with ranked resource list and total count.
        """
        if not query or not query.strip():
            return SearchResult(resources=[], total=0)

        return await self._full_text_search(
            session=session,
            owner_id=owner_id,
            query=query.strip(),
            tag=tag,
            limit=limit,
            offset=offset,
        )

    async def _full_text_search(
        self,
        session: AsyncSession,
        owner_id: UUID,
        query: str,
        tag: Optional[str],
        limit: int,
        offset: int,
    ) -> SearchResult:
        """
        Execute PostgreSQL full-text search using tsvector and ts_rank.

        Implementation follows design spec §4.3 with exact SQL from the design document.
        Uses the GIN index created in DEV-072 migration for efficient search.
        """
        sql = text(
            """
            SELECT *,
                   ts_rank("""
            + TSVECTOR_EXPRESSION  # nosec B608
            + """, plainto_tsquery('english', :query)) AS rank,
                   COUNT(*) OVER() AS total_count
            FROM resources
            WHERE owner_id = :owner_id
              AND status = 'READY'
              AND """
            + TSVECTOR_EXPRESSION  # nosec B608
            + """ @@ plainto_tsquery('english', :query)
              AND (:tag IS NULL OR jsonb_exists(tags, :tag))
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """
        ).bindparams(bindparam("tag", type_=String()))

        result = await session.execute(
            sql,
            {
                "query": query,
                "owner_id": str(owner_id),
                "tag": tag,
                "limit": limit,
                "offset": offset,
            },
        )

        rows = result.fetchall()
        total = rows[0].total_count if rows else 0
        items = [ResourceSearchItem.from_row(r) for r in rows]

        logger.info(
            f"Full-text search for owner_id={owner_id}, query='{query}', tag={tag}: "
            f"found {total} total, returning {len(items)} items"
        )

        return SearchResult(resources=items, total=total)


# Global instance
resource_search_service = ResourceSearchService()


def get_resource_search_service() -> ResourceSearchService:
    """Dependency function to get the resource search service."""
    return resource_search_service
