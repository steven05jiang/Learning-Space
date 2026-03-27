"""seed_system_categories

Revision ID: 2cc92e7b1ee7
Revises: f71b4e7e74fe
Create Date: 2026-03-27 00:09:21.558425

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2cc92e7b1ee7"
down_revision: Union[str, Sequence[str], None] = "f71b4e7e74fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_CATEGORIES = [
    "Science & Technology",
    "Business & Economics",
    "Politics & Government",
    "Society & Culture",
    "Education & Knowledge",
    "Health & Medicine",
    "Environment & Sustainability",
    "Arts & Entertainment",
    "Sports & Recreation",
    "Lifestyle & Personal Life",
]


def upgrade() -> None:
    """Seed system categories."""
    now = datetime.utcnow().isoformat()
    conn = op.get_bind()
    stmt = sa.text(
        "INSERT INTO categories (name, is_system, owner_id, created_at)"
        " VALUES (:name, TRUE, NULL, :now) ON CONFLICT DO NOTHING"
    )
    for name in SYSTEM_CATEGORIES:
        conn.execute(stmt, {"name": name, "now": now})


def downgrade() -> None:
    """Remove system categories."""
    op.execute("DELETE FROM categories WHERE is_system = TRUE AND owner_id IS NULL")
