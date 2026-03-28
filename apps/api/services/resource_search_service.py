"""
Resource search service for full-text search capabilities.

This service provides unified search functionality for both HTTP endpoints and
AI agent tools, using PostgreSQL full-text search with tsvector and ts_rank.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import String, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from services.embedding_service import embedding_service

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
        owner_id: int,
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

        query = query.strip()

        if settings.search_mode == "hybrid":
            items, total = await self._hybrid_search(
                session=session,
                owner_id=owner_id,
                query=query,
                tag=tag,
                limit=limit,
                offset=offset,
            )
        else:
            items, total = await self._full_text_search(
                session=session,
                owner_id=owner_id,
                query=query,
                tag=tag,
                limit=limit,
                offset=offset,
            )

        return SearchResult(resources=items, total=total)

    async def _full_text_search(
        self,
        session: AsyncSession,
        owner_id: int,
        query: str,
        tag: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[ResourceSearchItem], int]:
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
                "owner_id": owner_id,
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

        return items, total

    async def _embed(self, query: str) -> list[float]:
        """
        Generate embedding for the query using SiliconFlow.

        Args:
            query: Text to embed

        Returns:
            List of embedding values

        Raises:
            Exception: If embedding generation fails
        """
        return await embedding_service.generate_embedding(query)

    async def _vector_search(
        self,
        session: AsyncSession,
        owner_id: int,
        query_embedding: list[float],
        tag: Optional[str],
        limit: int,
    ) -> List[ResourceSearchItem]:
        """
        Execute vector search using pgvector cosine similarity.

        Args:
            session: AsyncSession for database operations
            owner_id: The authenticated user's ID
            query_embedding: Vector embedding for the query
            tag: Optional tag filter
            limit: Max results to return

        Returns:
            List of ResourceSearchItem with similarity as rank
        """
        sql = text("""
            SELECT r.*,
                   1 - (re.embedding <=> :query_embedding::vector) AS similarity
            FROM resources r
            JOIN resource_embeddings re ON re.resource_id = r.id
            WHERE r.owner_id = :owner_id
              AND r.status = 'READY'
              AND (:tag IS NULL OR jsonb_exists(r.tags, :tag))
            ORDER BY re.embedding <=> :query_embedding::vector
            LIMIT :limit
        """).bindparams(bindparam("tag", type_=String()))

        result = await session.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "owner_id": owner_id,
                "tag": tag,
                "limit": limit,
            },
        )

        rows = result.fetchall()
        items = []
        for row in rows:
            item = ResourceSearchItem.from_row(row)
            # Use similarity as rank for vector search
            item.rank = float(row.similarity)
            items.append(item)

        logger.info(
            f"Vector search for owner_id={owner_id}, tag={tag}: "
            f"found {len(items)} items"
        )

        return items

    async def _hybrid_search(
        self,
        session: AsyncSession,
        owner_id: int,
        query: str,
        tag: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[ResourceSearchItem], int]:
        """
        Execute hybrid search using RRF merge of full-text and vector results.

        Args:
            session: AsyncSession for database operations
            owner_id: The authenticated user's ID
            query: Search query string
            tag: Optional tag filter
            limit: Max results to return
            offset: Pagination offset

        Returns:
            Tuple of (items, total_count)
        """
        k = 60
        candidates = limit * 2

        try:
            # Get full-text search results
            full_text_items, _ = await self._full_text_search(
                session=session,
                owner_id=owner_id,
                query=query,
                tag=tag,
                limit=candidates,
                offset=0,
            )

            # Get embedding for the query
            query_embedding = await self._embed(query)
            if query_embedding is None:
                logger.warning(
                    f"Failed to generate embedding for query '{query}', falling back to full-text search"
                )
                # Fallback to full-text search
                return await self._full_text_search(
                    session=session,
                    owner_id=owner_id,
                    query=query,
                    tag=tag,
                    limit=limit,
                    offset=offset,
                )

            # Get vector search results
            vector_items = await self._vector_search(
                session=session,
                owner_id=owner_id,
                query_embedding=query_embedding,
                tag=tag,
                limit=candidates,
            )

            # RRF merge
            scores: dict = {}
            all_items: dict = {}

            # Add full-text scores
            for rank, item in enumerate(full_text_items):
                scores[item.id] = scores.get(item.id, 0.0) + 1.0 / (k + rank + 1)
                all_items[item.id] = item

            # Add vector scores
            for rank, item in enumerate(vector_items):
                scores[item.id] = scores.get(item.id, 0.0) + 1.0 / (k + rank + 1)
                all_items[item.id] = item

            # Sort by combined RRF score
            sorted_ids = sorted(scores, key=lambda i: scores[i], reverse=True)
            total = len(sorted_ids)

            # Apply pagination
            page = sorted_ids[offset:offset + limit]
            result = []
            for id_ in page:
                item = all_items[id_]
                item.rank = scores[id_]
                result.append(item)

            logger.info(
                f"Hybrid search for owner_id={owner_id}, query='{query}', tag={tag}: "
                f"merged {len(full_text_items)} full-text + {len(vector_items)} vector results, "
                f"returning {len(result)} items from {total} total"
            )

            return result, total

        except Exception as e:
            logger.warning(
                f"Hybrid search failed for query '{query}': {e}, falling back to full-text search"
            )
            # Fallback to full-text search
            return await self._full_text_search(
                session=session,
                owner_id=owner_id,
                query=query,
                tag=tag,
                limit=limit,
                offset=offset,
            )


# Global instance
resource_search_service = ResourceSearchService()


def get_resource_search_service() -> ResourceSearchService:
    """Dependency function to get the resource search service."""
    return resource_search_service
