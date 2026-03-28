"""add_resource_embeddings_table

Revision ID: 3987688a4c94
Revises: c88b95c7269d
Create Date: 2026-03-28 16:27:46.099758

Creates resource_embeddings table for vector similarity search with pgvector.
Includes IVFFlat index for approximate nearest-neighbor search with 2048-dim vectors.
"""

from typing import Sequence, Union

import sqlalchemy as sa
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

    # Create resource_embeddings table
    op.create_table(
        "resource_embeddings",
        sa.Column(
            "resource_id",
            sa.Integer(),
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "embedding", sa.String(), nullable=False
        ),  # vector(2048) - using String as placeholder
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Convert embedding column to vector(2048) type
    op.execute(
        text("ALTER TABLE resource_embeddings ALTER COLUMN embedding TYPE vector(2048)")
    )

    # Create IVFFlat index using autocommit_block (non-transactional DDL)
    with op.get_context().autocommit_block():
        op.execute(
            text(
                "CREATE INDEX CONCURRENTLY resource_embeddings_vec_idx "
                "ON resource_embeddings "
                "USING ivfflat (embedding vector_cosine_ops) "
                "WITH (lists = 100)"
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the IVFFlat index
    with op.get_context().autocommit_block():
        op.execute(
            text("DROP INDEX CONCURRENTLY IF EXISTS resource_embeddings_vec_idx")
        )

    # Drop the table (CASCADE will be handled by the FK constraint)
    op.drop_table("resource_embeddings")
