"""Test category rename migration (b3c4d5e6f7a8) logic and data transformations.

Validates the rename/merge map, JSON update logic, and deduplication without
requiring alembic to run — mirrors the pattern in test_migration_processing_status.py.
"""

import json

import pytest

# Import the migration module directly so constants stay in sync
import importlib.util
import pathlib

_MIGRATION_PATH = (
    pathlib.Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "b3c4d5e6f7a8_rename_system_categories_to_full_names.py"
)
_spec = importlib.util.spec_from_file_location("migration_categories", _MIGRATION_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

RENAME_MAP = _mod._RENAME_MAP
RESOURCE_OLD_TO_NEW = _mod._RESOURCE_OLD_TO_NEW
NEW_CATEGORIES = _mod._NEW_CATEGORIES

# The 10 canonical names from docs/design-category-taxonomy.md
CANONICAL_CATEGORIES = {
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
}


# ---------------------------------------------------------------------------
# Map correctness
# ---------------------------------------------------------------------------


def test_rename_map_produces_all_canonical_names():
    """Every target name in RENAME_MAP must be a canonical category."""
    targets = {v for v in RENAME_MAP.values() if v is not None}
    assert targets <= CANONICAL_CATEGORIES, (
        f"Unexpected target names in RENAME_MAP: {targets - CANONICAL_CATEGORIES}"
    )


def test_resource_old_to_new_produces_all_canonical_names():
    """Every target name in RESOURCE_OLD_TO_NEW must be a canonical category."""
    targets = set(RESOURCE_OLD_TO_NEW.values())
    assert targets <= CANONICAL_CATEGORIES, (
        f"Unexpected target names in RESOURCE_OLD_TO_NEW: {targets - CANONICAL_CATEGORIES}"
    )


def test_new_categories_are_canonical():
    """All newly-added categories must be canonical."""
    assert set(NEW_CATEGORIES) <= CANONICAL_CATEGORIES


def test_all_canonical_categories_are_reachable():
    """After applying rename + new inserts, all 10 canonical names must be present."""
    # Start with the old seed names
    old_names = set(RENAME_MAP.keys())
    # Apply renames (drop merged rows, keep renamed ones)
    after_rename = set()
    for old, new in RENAME_MAP.items():
        if new is not None:
            after_rename.add(new)
    # Add new inserts
    after_rename |= set(NEW_CATEGORIES)

    assert after_rename == CANONICAL_CATEGORIES, (
        f"Missing: {CANONICAL_CATEGORIES - after_rename}\n"
        f"Extra:   {after_rename - CANONICAL_CATEGORIES}"
    )


def test_merged_old_names_are_deleted():
    """Rows with None target (merged) must be deleted, not renamed."""
    deleted = {old for old, new in RENAME_MAP.items() if new is None}
    assert "Entertainment" in deleted
    assert "Science" in deleted
    assert "Philosophy" in deleted


# ---------------------------------------------------------------------------
# JSON update logic (Python simulation)
# ---------------------------------------------------------------------------


def _apply_resource_rename(categories: list[str]) -> list[str]:
    """Simulate the SQL JSON update logic in Python."""
    return [RESOURCE_OLD_TO_NEW.get(c, c) for c in categories]


def _deduplicate(categories: list[str]) -> list[str]:
    """Simulate the SQL deduplication step."""
    seen = set()
    result = []
    for c in sorted(set(categories)):  # ORDER BY elem
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def test_resource_rename_single_old_category():
    assert _apply_resource_rename(["Arts"]) == ["Arts & Entertainment"]
    assert _apply_resource_rename(["Business"]) == ["Business & Economics"]
    assert _apply_resource_rename(["Education"]) == ["Education & Knowledge"]
    assert _apply_resource_rename(["Entertainment"]) == ["Arts & Entertainment"]
    assert _apply_resource_rename(["Health"]) == ["Health & Medicine"]
    assert _apply_resource_rename(["Philosophy"]) == ["Society & Culture"]
    assert _apply_resource_rename(["Politics"]) == ["Politics & Government"]
    assert _apply_resource_rename(["Science"]) == ["Science & Technology"]
    assert _apply_resource_rename(["Sports"]) == ["Sports & Recreation"]
    assert _apply_resource_rename(["Technology"]) == ["Science & Technology"]


def test_resource_rename_already_canonical_is_noop():
    """Resources already using canonical names must not be changed."""
    for canonical in CANONICAL_CATEGORIES:
        assert _apply_resource_rename([canonical]) == [canonical]


def test_resource_rename_mixed_old_and_new():
    """Resources with a mix of old and new names are all updated correctly."""
    result = _apply_resource_rename(["Arts", "Science & Technology"])
    assert result == ["Arts & Entertainment", "Science & Technology"]


def test_deduplication_after_merge():
    """Resource with both 'Arts' and 'Entertainment' collapses to one entry."""
    renamed = _apply_resource_rename(["Arts", "Entertainment"])
    assert renamed == ["Arts & Entertainment", "Arts & Entertainment"]

    deduped = _deduplicate(renamed)
    assert deduped == ["Arts & Entertainment"]
    assert len(deduped) == 1


def test_deduplication_after_science_technology_merge():
    """Resource with both 'Science' and 'Technology' collapses to one entry."""
    renamed = _apply_resource_rename(["Science", "Technology"])
    deduped = _deduplicate(renamed)
    assert deduped == ["Science & Technology"]


def test_no_data_loss_for_distinct_categories():
    """Resources with non-overlapping old categories keep all entries after rename."""
    renamed = _apply_resource_rename(["Arts", "Business", "Education"])
    deduped = _deduplicate(renamed)
    assert set(deduped) == {
        "Arts & Entertainment",
        "Business & Economics",
        "Education & Knowledge",
    }
    assert len(deduped) == 3


def test_resources_are_never_deleted():
    """The migration only updates category names; no resources are deleted."""
    # Verify RESOURCE_OLD_TO_NEW covers every old name (no row is silently dropped)
    for old_name in RENAME_MAP:
        assert old_name in RESOURCE_OLD_TO_NEW, (
            f"'{old_name}' is in RENAME_MAP but missing from RESOURCE_OLD_TO_NEW — "
            "resources with this category would not be updated"
        )


# ---------------------------------------------------------------------------
# Integration: model-level check (no DB required)
# ---------------------------------------------------------------------------


def test_category_model_exists():
    """Category model is importable and has the expected fields."""
    from models.category import Category

    assert hasattr(Category, "name")
    assert hasattr(Category, "is_system")
    assert hasattr(Category, "owner_id")
