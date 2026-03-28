"""Embedding service for generating vector embeddings using SiliconFlow."""

import logging
from typing import Optional

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.resource import Resource

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing resource embeddings."""

    def __init__(self):
        """Initialize the embedding service with SiliconFlow client."""
        self.client = OpenAI(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
        )

    def build_embedding_text(self, resource: Resource) -> str:
        """Concatenate searchable fields for embedding generation.

        Args:
            resource: The resource to build embedding text for

        Returns:
            Concatenated text for embedding
        """
        parts = []
        if resource.title:
            parts.append(resource.title)
        if resource.summary:
            parts.append(resource.summary)
        if resource.tags:
            parts.append(" ".join(resource.tags))
        if resource.top_level_categories:
            parts.append(" ".join(resource.top_level_categories))
        return " ".join(parts)

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        """Generate embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            List of embedding values or None if failed

        Raises:
            Exception: If embedding generation fails critically
        """
        if not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None

        try:
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )

            if response.data:
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("Empty response data from embedding API")
                return None

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def upsert_resource_embedding(
        self,
        session: AsyncSession,
        resource_id: int,
        embedding: list[float],
        model: str = None,
    ) -> None:
        """Insert or update the embedding row for a resource.

        Args:
            session: Database session
            resource_id: ID of the resource
            embedding: Embedding vector
            model: Model used for embedding (defaults to config value)
        """
        model = model or settings.embedding_model

        # Use raw SQL for upsert with vector type
        from sqlalchemy import text

        await session.execute(
            text("""
                INSERT INTO resource_embeddings (
                    resource_id, embedding, model, created_at, updated_at
                )
                VALUES (:resource_id, :embedding, :model, now(), now())
                ON CONFLICT (resource_id)
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    model = EXCLUDED.model,
                    updated_at = now()
            """),
            {
                "resource_id": resource_id,
                "embedding": embedding,
                "model": model,
            },
        )
        await session.commit()
        logger.info(f"Upserted embedding for resource {resource_id}")


# Singleton instance
embedding_service = EmbeddingService()
