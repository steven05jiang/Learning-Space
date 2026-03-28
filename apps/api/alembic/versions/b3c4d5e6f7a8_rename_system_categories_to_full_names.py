"""rename system categories to full canonical names

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28 00:00:00.000000

The initial migration seeded short names ("Arts", "Business", "Education"…)
that don't match the design spec or the LLM prompt's expected category list.
This migration renames them to the canonical full names and updates all
resources.top_level_categories JSON references accordingly.

Rename / merge map:
  Arts         → Arts & Entertainment
  Business     → Business & Economics
  Education    → Education & Knowledge
  Entertainment→ (merged into Arts & Entertainment, row deleted)
  Health       → Health & Medicine
  Philosophy   → (replaced by Society & Culture, row deleted)
  Politics     → Politics & Government
  Science      → (merged into Science & Technology, row deleted)
  Sports       → Sports & Recreation
  Technology   → Science & Technology

New categories added (were missing from the original seed):
  Society & Culture
  Environment & Sustainability
  Lifestyle & Personal Life
"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Old name → new canonical name (None = delete row, merged into another)
_RENAME_MAP = {
    "Arts": "Arts & Entertainment",
    "Business": "Business & Economics",
    "Education": "Education & Knowledge",
    "Entertainment": None,  # merged into Arts & Entertainment
    "Health": "Health & Medicine",
    "Philosophy": None,  # replaced by Society & Culture
    "Politics": "Politics & Government",
    "Science": None,  # merged into Science & Technology
    "Sports": "Sports & Recreation",
    "Technology": "Science & Technology",
}

# The old name that will be renamed to carry the merged canonical name
_RESOURCE_OLD_TO_NEW = {
    "Arts": "Arts & Entertainment",
    "Business": "Business & Economics",
    "Education": "Education & Knowledge",
    "Entertainment": "Arts & Entertainment",
    "Health": "Health & Medicine",
    "Philosophy": "Society & Culture",
    "Politics": "Politics & Government",
    "Science": "Science & Technology",
    "Sports": "Sports & Recreation",
    "Technology": "Science & Technology",
}

_NEW_CATEGORIES = [
    "Society & Culture",
    "Environment & Sustainability",
    "Lifestyle & Personal Life",
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Rename categories that map 1-to-1 (no merge conflict)
    for old, new in _RENAME_MAP.items():
        if new is not None:
            conn.execute(
                text(
                    "UPDATE categories SET name = :new "
                    "WHERE name = :old AND owner_id IS NULL"
                ),
                {"old": old, "new": new},
            )

    # 2. Delete rows that were merged into a renamed category
    for old, new in _RENAME_MAP.items():
        if new is None:
            conn.execute(
                text("DELETE FROM categories WHERE name = :old AND owner_id IS NULL"),
                {"old": old},
            )

    # 3. Insert missing canonical system categories (idempotent)
    for name in _NEW_CATEGORIES:
        conn.execute(
            text(
                "INSERT INTO categories (name, is_system, owner_id, created_at) "
                "VALUES (:name, true, NULL, NOW()) "
                "ON CONFLICT DO NOTHING"
            ),
            {"name": name},
        )

    # 4. Update resources.top_level_categories JSON arrays
    #    Replace each old string value with the canonical new name.
    #    Uses jsonb_agg + jsonb_array_elements_text to rebuild the array.
    for old, new in _RESOURCE_OLD_TO_NEW.items():
        conn.execute(
            text("""
                UPDATE resources
                SET top_level_categories = (
                    SELECT jsonb_agg(
                        CASE
                            WHEN elem = :old THEN :new::text
                            ELSE elem
                        END
                    )
                    FROM jsonb_array_elements_text(top_level_categories) AS elem
                )
                WHERE top_level_categories IS NOT NULL
                  AND top_level_categories @> :old_json::jsonb
            """),
            {"old": old, "new": new, "old_json": f'["{old}"]'},
        )

    # 5. Deduplicate any resources that now have duplicate categories
    #    (e.g. a resource that had both "Arts" and "Entertainment" now has
    #     "Arts & Entertainment" twice — collapse to distinct values).
    conn.execute(
        text("""
        UPDATE resources
        SET top_level_categories = (
            SELECT jsonb_agg(DISTINCT elem ORDER BY elem)
            FROM jsonb_array_elements_text(top_level_categories) AS elem
        )
        WHERE top_level_categories IS NOT NULL
          AND jsonb_array_length(top_level_categories) > (
              SELECT count(DISTINCT elem)
              FROM jsonb_array_elements_text(top_level_categories) AS elem
          )
    """)
    )


def downgrade() -> None:
    # Reverse is impractical (merged rows cannot be un-merged), but provided
    # for completeness so Alembic doesn't error on downgrade.
    conn = op.get_bind()

    # Remove newly-added categories
    for name in _NEW_CATEGORIES:
        conn.execute(
            text("DELETE FROM categories WHERE name = :name AND owner_id IS NULL"),
            {"name": name},
        )

    # Rename canonical names back to short names (best-effort; merges are lost)
    for old, new in _RENAME_MAP.items():
        if new is not None:
            conn.execute(
                text(
                    "UPDATE categories SET name = :old "
                    "WHERE name = :new AND owner_id IS NULL"
                ),
                {"old": old, "new": new},
            )

    # Re-seed deleted rows
    for old, new in _RENAME_MAP.items():
        if new is None:
            conn.execute(
                text(
                    "INSERT INTO categories (name, is_system, owner_id, created_at) "
                    "VALUES (:name, true, NULL, NOW()) ON CONFLICT DO NOTHING"
                ),
                {"name": old},
            )

    # Reverse resource JSON updates (best-effort; duplicates from merges are lost)
    for old, new in _RESOURCE_OLD_TO_NEW.items():
        conn.execute(
            text("""
                UPDATE resources
                SET top_level_categories = (
                    SELECT jsonb_agg(
                        CASE WHEN elem = :new THEN :old::text ELSE elem END
                    )
                    FROM jsonb_array_elements_text(top_level_categories) AS elem
                )
                WHERE top_level_categories IS NOT NULL
                  AND top_level_categories @> :new_json::jsonb
            """),
            {"old": old, "new": new, "new_json": f'["{new}"]'},
        )
