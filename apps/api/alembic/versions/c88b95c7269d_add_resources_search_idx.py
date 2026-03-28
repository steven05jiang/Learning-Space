"""add_resources_search_idx

Revision ID: c88b95c7269d
Revises: b3c4d5e6f7a8
Create Date: 2026-03-28 12:16:16.141957

Creates a functional GIN index on resources table for full-text search.
The index covers title, summary, and tags fields via to_tsvector expression.
"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c88b95c7269d"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create GIN functional index for full-text search
    # Using CONCURRENTLY to avoid table lock in production
    with op.get_context().autocommit_block():
        op.execute(
            text(
                "CREATE INDEX CONCURRENTLY resources_search_idx "
                "ON resources USING GIN ("
                "to_tsvector('english', "
                "COALESCE(title,'') || ' ' || "
                "COALESCE(summary,'') || ' ' || "
                "COALESCE(tags::text,'[]')))"
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the GIN index
    # Using CONCURRENTLY to avoid table lock in production
    with op.get_context().autocommit_block():
        op.execute(text("DROP INDEX CONCURRENTLY IF EXISTS resources_search_idx"))
