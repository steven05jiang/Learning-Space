"""
Tests for GraphService.
"""

import contextlib
from unittest.mock import AsyncMock, patch

import pytest

from services.graph_service import GraphService


@pytest.fixture
def graph_service():
    """Create a fresh GraphService instance for testing."""
    return GraphService()


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver."""
    mock_driver = AsyncMock()
    mock_session = AsyncMock()

    # Mock the driver.get_session() to return an async context manager
    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.get_session = lambda: mock_session_context()
    return mock_driver, mock_session


@pytest.mark.asyncio
async def test_update_from_resource_creates_tags_and_relationships(graph_service, mock_neo4j_driver):
    """Test that update_from_resource creates Tag nodes and RELATED_TO relationships."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_from_resource(
            owner_id=1,
            tags=["python", "programming", "tutorial"]
        )

        # Verify Tag node creation calls (3 tags = 3 calls)
        assert mock_session.run.call_count == 6  # 3 tag creations + 3 relationship creations

        # Verify Tag node creation queries
        tag_creation_calls = mock_session.run.call_args_list[:3]
        for i, call in enumerate(tag_creation_calls):
            query = call[0][0]
            assert "MERGE (t:Tag {name: $tag, owner_id: $owner_id})" in query
            assert "ON CREATE SET t.created_at = datetime()" in query

        # Verify relationship creation queries
        relationship_calls = mock_session.run.call_args_list[3:]
        for call in relationship_calls:
            query = call[0][0]
            assert "MATCH (t1:Tag {name: $tag1, owner_id: $owner_id})" in query
            assert "MATCH (t2:Tag {name: $tag2, owner_id: $owner_id})" in query
            assert "MERGE (t1)-[r:RELATED_TO]-(t2)" in query
            assert "ON CREATE SET r.weight = 1" in query
            assert "ON MATCH SET r.weight = r.weight + 1" in query


@pytest.mark.asyncio
async def test_update_from_resource_skips_insufficient_tags(graph_service, mock_neo4j_driver):
    """Test that update_from_resource skips processing when less than 2 tags."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        # Test with no tags
        await graph_service.update_from_resource(owner_id=1, tags=[])
        assert mock_session.run.call_count == 0

        # Test with one tag
        await graph_service.update_from_resource(owner_id=1, tags=["python"])
        assert mock_session.run.call_count == 0

        # Test with empty strings
        await graph_service.update_from_resource(owner_id=1, tags=["python", "", "  "])
        assert mock_session.run.call_count == 0


@pytest.mark.asyncio
async def test_update_from_resource_normalizes_tags(graph_service, mock_neo4j_driver):
    """Test that update_from_resource normalizes tags by stripping whitespace."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_from_resource(
            owner_id=1,
            tags=["  python  ", "programming", "  tutorial  "]
        )

        # Verify that tags were normalized in the calls
        calls = mock_session.run.call_args_list
        tag_creation_calls = calls[:3]

        tag_names = []
        for call in tag_creation_calls:
            kwargs = call[1]
            tag_names.append(kwargs["tag"])

        assert "python" in tag_names
        assert "programming" in tag_names
        assert "tutorial" in tag_names
        assert "  python  " not in tag_names


@pytest.mark.asyncio
async def test_remove_resource_tags_decrements_weights(graph_service, mock_neo4j_driver):
    """Test that remove_resource_tags decrements relationship weights."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.remove_resource_tags(
            owner_id=1,
            old_tags=["python", "programming", "tutorial"]
        )

        # Should have 3 calls for the 3 tag pairs: (python,programming), (python,tutorial), (programming,tutorial)
        assert mock_session.run.call_count == 3

        # Verify decrement and delete queries
        for call in mock_session.run.call_args_list:
            query = call[0][0]
            assert "MATCH (t1:Tag {name: $tag1, owner_id: $owner_id})-[r:RELATED_TO]-(t2:Tag {name: $tag2, owner_id: $owner_id})" in query
            assert "SET r.weight = r.weight - 1" in query
            assert "WHERE r.weight <= 0" in query
            assert "DELETE r" in query


@pytest.mark.asyncio
async def test_remove_resource_tags_skips_insufficient_tags(graph_service, mock_neo4j_driver):
    """Test that remove_resource_tags skips processing when less than 2 tags."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        # Test with no tags
        await graph_service.remove_resource_tags(owner_id=1, old_tags=[])
        assert mock_session.run.call_count == 0

        # Test with one tag
        await graph_service.remove_resource_tags(owner_id=1, old_tags=["python"])
        assert mock_session.run.call_count == 0


@pytest.mark.asyncio
async def test_cleanup_orphan_tags_removes_unconnected_tags(graph_service, mock_neo4j_driver):
    """Test that cleanup_orphan_tags removes Tag nodes with no relationships."""
    mock_driver, mock_session = mock_neo4j_driver

    # Mock the result of the cleanup query
    mock_result = AsyncMock()
    mock_record = {"deleted_count": 2, "deleted_tags": ["orphan1", "orphan2"]}
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.cleanup_orphan_tags(owner_id=1)

        # Verify cleanup query was called
        assert mock_session.run.call_count == 1
        query = mock_session.run.call_args[0][0]
        assert "MATCH (t:Tag {owner_id: $owner_id})" in query
        assert "WHERE NOT (t)-[:RELATED_TO]-()" in query
        assert "DELETE t" in query
        assert "RETURN COUNT(*) AS deleted_count, COLLECT(tag_name) AS deleted_tags" in query


@pytest.mark.asyncio
async def test_cleanup_orphan_tags_handles_no_orphans(graph_service, mock_neo4j_driver):
    """Test that cleanup_orphan_tags handles the case where no orphans exist."""
    mock_driver, mock_session = mock_neo4j_driver

    # Mock the result with no deletions
    mock_result = AsyncMock()
    mock_record = {"deleted_count": 0, "deleted_tags": []}
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.cleanup_orphan_tags(owner_id=1)

        # Should still call the cleanup query
        assert mock_session.run.call_count == 1


@pytest.mark.asyncio
async def test_get_tag_relationships_returns_formatted_results(graph_service, mock_neo4j_driver):
    """Test that get_tag_relationships returns properly formatted relationship data."""
    mock_driver, mock_session = mock_neo4j_driver

    # Mock the result of the relationships query
    mock_result = AsyncMock()
    mock_records = [
        {"tag1": "python", "tag2": "programming", "weight": 3},
        {"tag1": "programming", "tag2": "tutorial", "weight": 2},
        {"tag1": "python", "tag2": "tutorial", "weight": 1},
    ]

    async def async_iter(self):
        for record in mock_records:
            yield record

    mock_result.__aiter__ = async_iter
    mock_session.run.return_value = mock_result

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        relationships = await graph_service.get_tag_relationships(owner_id=1)

        # Verify query was called
        assert mock_session.run.call_count == 1
        query = mock_session.run.call_args[0][0]
        assert "MATCH (t1:Tag {owner_id: $owner_id})-[r:RELATED_TO]-(t2:Tag {owner_id: $owner_id})" in query
        assert "WHERE t1.name < t2.name" in query
        assert "RETURN t1.name AS tag1, t2.name AS tag2, r.weight AS weight" in query

        # Verify returned data format
        assert len(relationships) == 3
        assert relationships[0] == {"tag1": "python", "tag2": "programming", "weight": 3}
        assert relationships[1] == {"tag1": "programming", "tag2": "tutorial", "weight": 2}
        assert relationships[2] == {"tag1": "python", "tag2": "tutorial", "weight": 1}


@pytest.mark.asyncio
async def test_update_from_resource_with_two_tags(graph_service, mock_neo4j_driver):
    """Test that update_from_resource works correctly with exactly 2 tags."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_from_resource(
            owner_id=1,
            tags=["python", "programming"]
        )

        # Should have 3 calls: 2 tag creations + 1 relationship creation
        assert mock_session.run.call_count == 3


@pytest.mark.asyncio
async def test_owner_id_scoping_in_queries(graph_service, mock_neo4j_driver):
    """Test that all queries properly scope by owner_id."""
    mock_driver, mock_session = mock_neo4j_driver

    owner_id = 42

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        # Test update_from_resource
        await graph_service.update_from_resource(
            owner_id=owner_id,
            tags=["tag1", "tag2"]
        )

        # Verify all calls include the correct owner_id
        for call in mock_session.run.call_args_list:
            kwargs = call[1]
            assert kwargs["owner_id"] == owner_id

        # Reset mock for next test
        mock_session.reset_mock()

        # Test remove_resource_tags
        await graph_service.remove_resource_tags(
            owner_id=owner_id,
            old_tags=["tag1", "tag2"]
        )

        for call in mock_session.run.call_args_list:
            kwargs = call[1]
            assert kwargs["owner_id"] == owner_id