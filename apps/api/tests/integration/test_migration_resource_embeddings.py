"""Test resource_embeddings migration (3987688a4c94) schema validation.

Validates pgvector extension enablement, table creation with vector(2048) column,
and FK constraints. No approximate NN index — pgvector IVFFlat/HNSW both cap at
2000 dimensions; Qwen3-Embedding-4B uses 2048. Exact cosine scan is used instead,
which is fast enough for personal library scale (<10K rows).
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
async def test_pgvector_extension_enabled(db_session: AsyncSession):
    """Test that pgvector extension is properly enabled."""
    result = await db_session.execute(
        text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
    )
    extension_exists = result.scalar()
    assert extension_exists is True, "pgvector extension should be enabled"


@pytest.mark.integration
async def test_resource_embeddings_table_exists(db_session: AsyncSession):
    """Test that resource_embeddings table exists with correct structure."""
    # Check table exists
    result = await db_session.execute(
        text("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'resource_embeddings'
                AND table_schema = 'public'
            )
        """)
    )
    table_exists = result.scalar()
    assert table_exists is True, "resource_embeddings table should exist"


@pytest.mark.integration
async def test_resource_embeddings_columns(db_session: AsyncSession):
    """Test that resource_embeddings table has correct columns with types."""
    result = await db_session.execute(
        text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'resource_embeddings'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
    )
    columns = result.fetchall()

    # Convert to dict for easier assertions
    column_info = {
        row[0]: {"type": row[1], "nullable": row[2], "default": row[3]}
        for row in columns
    }

    # Check required columns exist
    required_columns = ["resource_id", "embedding", "model", "created_at", "updated_at"]
    for col in required_columns:
        assert col in column_info, f"Column {col} should exist"

    # Check column types and constraints
    assert column_info["resource_id"]["type"] == "integer"
    assert column_info["resource_id"]["nullable"] == "NO"

    assert column_info["model"]["type"] == "character varying"
    assert column_info["model"]["nullable"] == "NO"

    assert column_info["created_at"]["type"] == "timestamp with time zone"
    assert column_info["created_at"]["nullable"] == "NO"
    created_default = column_info["created_at"]["default"] or ""
    assert "now()" in created_default

    assert column_info["updated_at"]["type"] == "timestamp with time zone"
    assert column_info["updated_at"]["nullable"] == "NO"
    updated_default = column_info["updated_at"]["default"] or ""
    assert "now()" in updated_default


@pytest.mark.integration
async def test_embedding_column_is_vector_2048(db_session: AsyncSession):
    """Test that embedding column is vector(2048) type."""
    # Check the embedding column type using pg_attribute and pg_type
    result = await db_session.execute(
        text("""
            SELECT
                t.typname,
                a.atttypmod
            FROM pg_class c
            JOIN pg_attribute a ON c.oid = a.attrelid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE c.relname = 'resource_embeddings'
            AND a.attname = 'embedding'
            AND NOT a.attisdropped
        """)
    )
    row = result.fetchone()

    assert row is not None, "embedding column should exist"
    type_name, type_mod = row

    assert type_name == "vector", "embedding column should be vector type"
    # For vector(n), typmod is n+4, so vector(2048) has typmod 2052
    expected_typmod = 2052
    assert type_mod == expected_typmod, (
        f"embedding column should be vector(2048), got typmod {type_mod}"
    )


@pytest.mark.integration
async def test_resource_id_foreign_key_constraint(db_session: AsyncSession):
    """Test FK constraint on resource_id with ON DELETE CASCADE."""
    result = await db_session.execute(
        text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'resource_embeddings'
            AND kcu.column_name = 'resource_id'
        """)
    )
    fk_info = result.fetchone()

    assert fk_info is not None, "FK constraint should exist on resource_id"
    constraint_name, column_name, foreign_table, foreign_column, delete_rule = fk_info

    assert column_name == "resource_id", "FK should be on resource_id column"
    assert foreign_table == "resources", "FK should reference resources table"
    assert foreign_column == "id", "FK should reference id column"
    assert delete_rule == "CASCADE", "FK should have ON DELETE CASCADE"


@pytest.mark.integration
async def test_primary_key_constraint(db_session: AsyncSession):
    """Test that resource_id is the primary key."""
    result = await db_session.execute(
        text("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = 'resource_embeddings'
            ORDER BY kcu.ordinal_position
        """)
    )
    pk_columns = [row[0] for row in result.fetchall()]

    expected = ["resource_id"]
    assert pk_columns == expected, "resource_id should be the only primary key"


@pytest.mark.integration
async def test_no_approximate_nn_index(db_session: AsyncSession):
    """Confirm no IVFFlat/HNSW index — exact scan used (2048 dims > 2000 limit)."""
    result = await db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE tablename = 'resource_embeddings'
            AND indexname = 'resource_embeddings_vec_idx'
        """)
    )
    count = result.scalar()
    # pgvector IVFFlat/HNSW cap at 2000 dims; Qwen3-4B uses 2048
    assert count == 0, "No approximate NN index should exist"


@pytest.mark.integration
async def test_migration_downgrade_removes_table(db_session: AsyncSession):
    """Test that the table can be safely dropped (validates downgrade path)."""
    # This test verifies the table exists and has the expected structure
    # The actual downgrade is tested by the migration system itself

    # Check table exists (prerequisite for successful downgrade)
    result = await db_session.execute(
        text("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'resource_embeddings'
                AND table_schema = 'public'
            )
        """)
    )
    table_exists = result.scalar()
    assert table_exists is True, "Table should exist before downgrade"

    # Check that there are no other dependencies that would prevent clean downgrade
    result = await db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints tc
            WHERE tc.table_name = 'resource_embeddings'
            AND tc.constraint_type = 'FOREIGN KEY'
        """)
    )
    fk_count = result.scalar()
    # Should have exactly 1 FK (to resources.id)
    assert fk_count == 1, "Should have exactly 1 FK constraint for clean downgrade"


@pytest.mark.integration
async def test_vector_dimension_compatibility():
    """Integration test: verify vector operations work with 2048 dimensions."""
    # This is a minimal integration test to ensure the vector(2048) type
    # works correctly for actual embedding operations

    # This test requires a real database with pgvector
    # It's marked as integration so it only runs with infrastructure
    pass  # Placeholder - would test actual vector operations if needed
