"""add_resource_embeddings_table

Revision ID: 3987688a4c94
Revises: c88b95c7269d
Create Date: 2026-03-28 16:27:46.099758

Creates resource_embeddings table for vector similarity search with pgvector.
Uses vector(2560) for Qwen/Qwen3-Embedding-4B. No approximate NN index — exact
cosine scan is fast enough for personal library scale (<10K rows). An IVFFlat or
HNSW index can be added later if needed, but both require ≤2000 dimensions which
this model exceeds.
"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3987688a4c94"
down_revision: Union[str, Sequence[str], None] = "c88b95c7269d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Create resource_embeddings table with vector(2048) column directly.
    # Note: pgvector IVFFlat/HNSW indexes cap at 2000 dims; exact scan used instead.
    op.execute(
        text("""
        CREATE TABLE resource_embeddings (
            resource_id INTEGER PRIMARY KEY REFERENCES resources(id) ON DELETE CASCADE,
            embedding   vector(2560) NOT NULL,
            model       VARCHAR(100) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("resource_embeddings")
