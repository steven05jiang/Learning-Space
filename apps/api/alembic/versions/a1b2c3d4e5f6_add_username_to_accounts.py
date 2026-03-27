"""Add username to accounts table

Revision ID: a1b2c3d4e5f6
Revises: 2cc92e7b1ee7
Create Date: 2026-03-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2cc92e7b1ee7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("username", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "username")
