"""add top_level_categories to resources table

Revision ID: f71b4e7e74fe
Revises: d6c000ccd5ba
Create Date: 2026-03-26 20:43:48.638679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'f71b4e7e74fe'
down_revision: Union[str, Sequence[str], None] = 'd6c000ccd5ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add top_level_categories column to resources table."""
    # Add the top_level_categories column as JSONB, defaulting to empty array
    op.add_column('resources', sa.Column(
        'top_level_categories',
        JSONB,
        nullable=False,
        server_default='[]'
    ))


def downgrade() -> None:
    """Remove top_level_categories column from resources table."""
    op.drop_column('resources', 'top_level_categories')
