"""add_embedding_status_to_resources

Revision ID: e1f2a3b4c5d6
Revises: 9a9a6bde9933
Create Date: 2026-03-29

Adds embedding_status column to resources table.
Values: none | processing | ready

Backfills 'ready' for any resource that already has a row in resource_embeddings.
"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "9a9a6bde9933"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        text("CREATE TYPE embeddingstatus AS ENUM ('none', 'processing', 'ready')")
    )
    op.execute(
        text("""
        ALTER TABLE resources
        ADD COLUMN embedding_status embeddingstatus NOT NULL DEFAULT 'none'
    """)
    )
    # Backfill: resources that already have an embedding row are 'ready'
    op.execute(
        text("""
        UPDATE resources
        SET embedding_status = 'ready'
        WHERE id IN (SELECT resource_id FROM resource_embeddings)
    """)
    )


def downgrade() -> None:
    op.execute(text("ALTER TABLE resources DROP COLUMN embedding_status"))
    op.execute(text("DROP TYPE embeddingstatus"))
