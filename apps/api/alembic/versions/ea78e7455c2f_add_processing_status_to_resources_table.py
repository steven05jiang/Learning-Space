"""add processing_status to resources table

Revision ID: ea78e7455c2f
Revises: 111e5b3d61af
Create Date: 2026-03-25 22:25:48.164695

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea78e7455c2f"
down_revision: Union[str, Sequence[str], None] = "111e5b3d61af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type
    processing_status_enum = sa.Enum(
        "pending", "processing", "success", "failed", name="processingstatus"
    )
    processing_status_enum.create(op.get_bind())

    # Add column with default value
    op.add_column(
        "resources",
        sa.Column(
            "processing_status",
            processing_status_enum,
            nullable=False,
            server_default="pending",
        ),
    )

    # Backfill existing rows based on status column
    # status=READY → processing_status=success
    # status=FAILED → processing_status=failed
    # all others → processing_status=pending
    op.execute("""
        UPDATE resources
        SET processing_status = CASE
            WHEN status = 'READY' THEN 'success'
            WHEN status = 'FAILED' THEN 'failed'
            ELSE 'pending'
        END
    """)

    # Remove server default after backfill
    op.alter_column("resources", "processing_status", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop column
    op.drop_column("resources", "processing_status")

    # Drop enum type
    sa.Enum(name="processingstatus").drop(op.get_bind())
