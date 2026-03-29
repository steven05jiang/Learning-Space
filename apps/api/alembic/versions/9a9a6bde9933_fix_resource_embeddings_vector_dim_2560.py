"""fix_resource_embeddings_vector_dim_2560

Revision ID: 9a9a6bde9933
Revises: 3987688a4c94
Create Date: 2026-03-28 22:06:02.051614

Qwen3-Embedding-4B produces 2560-dimensional vectors, not 2048.
ALTER the column type to match actual model output.
"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

revision: str = "9a9a6bde9933"
down_revision: Union[str, Sequence[str], None] = "3987688a4c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # USING NULL resets any existing rows to NULL, allowing the type change
    # regardless of the old dimension. Safe even on empty tables.
    op.execute(
        text(
            "ALTER TABLE resource_embeddings "
            "ALTER COLUMN embedding TYPE vector(2560) USING NULL"
        )
    )


def downgrade() -> None:
    op.execute(
        text(
            "ALTER TABLE resource_embeddings "
            "ALTER COLUMN embedding TYPE vector(2048) USING NULL"
        )
    )
