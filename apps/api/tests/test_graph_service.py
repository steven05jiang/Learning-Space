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
async def test_update_from_resource_creates_tags_and_relationships(
    graph_service, mock_neo4j_driver
):
    """Test that update_from_resource creates Tag nodes and RELATED_TO relationships."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_from_resource(
            owner_id=1, tags=["python", "programming", "tutorial"]
        )

        # Verify Tag node creation calls (3 tags = 3 calls)
        # 3 tag creations + 3 relationship creations
        assert mock_session.run.call_count == 6

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
async def test_update_from_resource_skips_insufficient_tags(
    graph_service, mock_neo4j_driver
):
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
            owner_id=1, tags=["  python  ", "programming", "  tutorial  "]
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
async def test_remove_resource_tags_decrements_weights(
    graph_service, mock_neo4j_driver
):
    """Test that remove_resource_tags decrements relationship weights."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.remove_resource_tags(
            owner_id=1, old_tags=["python", "programming", "tutorial"]
        )

        # Should have 3 calls for the 3 tag pairs:
        # (python,programming), (python,tutorial), (programming,tutorial)
        assert mock_session.run.call_count == 3

        # Verify decrement and delete queries
        for call in mock_session.run.call_args_list:
            query = call[0][0]
            assert "MATCH (t1:Tag {name: $tag1, owner_id: $owner_id})" in query
            assert "-[r:RELATED_TO]-" in query
            assert "(t2:Tag {name: $tag2, owner_id: $owner_id})" in query
            assert "SET r.weight = r.weight - 1" in query
            assert "WHERE r.weight <= 0" in query
            assert "DELETE r" in query


@pytest.mark.asyncio
async def test_remove_resource_tags_skips_insufficient_tags(
    graph_service, mock_neo4j_driver
):
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
async def test_cleanup_orphan_tags_removes_unconnected_tags(
    graph_service, mock_neo4j_driver
):
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
        expected_return = (
            "RETURN COUNT(*) AS deleted_count, COLLECT(tag_name) AS deleted_tags"
        )
        assert expected_return in query


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
async def test_get_tag_relationships_returns_formatted_results(
    graph_service, mock_neo4j_driver
):
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
        assert "MATCH (t1:Tag {owner_id: $owner_id})" in query
        assert "-[r:RELATED_TO]-" in query
        assert "(t2:Tag {owner_id: $owner_id})" in query
        assert "WHERE t1.name < t2.name" in query
        assert "RETURN t1.name AS tag1, t2.name AS tag2, r.weight AS weight" in query

        # Verify returned data format
        assert len(relationships) == 3
        expected_rel_0 = {"tag1": "python", "tag2": "programming", "weight": 3}
        expected_rel_1 = {"tag1": "programming", "tag2": "tutorial", "weight": 2}
        assert relationships[0] == expected_rel_0
        assert relationships[1] == expected_rel_1
        assert relationships[2] == {"tag1": "python", "tag2": "tutorial", "weight": 1}


@pytest.mark.asyncio
async def test_update_from_resource_with_two_tags(graph_service, mock_neo4j_driver):
    """Test that update_from_resource works correctly with exactly 2 tags."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_from_resource(
            owner_id=1, tags=["python", "programming"]
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
            owner_id=owner_id, tags=["tag1", "tag2"]
        )

        # Verify all calls include the correct owner_id (converted to string)
        for call in mock_session.run.call_args_list:
            kwargs = call[1]
            assert kwargs["owner_id"] == str(owner_id)

        # Reset mock for next test
        mock_session.reset_mock()

        # Test remove_resource_tags
        await graph_service.remove_resource_tags(
            owner_id=owner_id, old_tags=["tag1", "tag2"]
        )

        for call in mock_session.run.call_args_list:
            kwargs = call[1]
            assert kwargs["owner_id"] == str(owner_id)


@pytest.mark.asyncio
async def test_update_graph_creates_hierarchical_structure(
    graph_service, mock_neo4j_driver
):
    """Test that update_graph creates Root, Category, and Tag nodes."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=1,
            tags=["machine-learning", "ai", "python"],
            top_level_categories=["Science & Technology", "Education & Knowledge"],
        )

        # Expected calls:
        # 1. Create Root node
        # 2-3. Create Category nodes (2 categories)
        # 4-6. Create Tag nodes (3 tags)
        # 7-12. Create BELONGS_TO relationships (3 tags × 2 categories = 6)
        # 13-15. Create RELATED_TO relationships (3 tags, 3 pairs)
        # Total: 15 calls
        assert mock_session.run.call_count == 15

        # Verify Root node creation
        root_call = mock_session.run.call_args_list[0]
        query = root_call[0][0]
        assert "MERGE (r:Root {owner_id: $owner_id})" in query
        assert "r.name = 'My Learning Space'" in query
        assert "r.node_type = 'root'" in query

        # Verify Category node creation
        category_calls = mock_session.run.call_args_list[1:3]
        for call in category_calls:
            query = call[0][0]
            assert "MERGE (c:Category {id: $category, owner_id: $owner_id})" in query
            assert "c.node_type = 'category'" in query
            assert "MERGE (c)-[:CHILD_OF]->(r)" in query

        # Verify Tag node creation
        tag_calls = mock_session.run.call_args_list[3:6]
        for call in tag_calls:
            query = call[0][0]
            assert "MERGE (t:Tag {id: $tag, owner_id: $owner_id})" in query
            assert "t.node_type = 'topic'" in query

        # Verify BELONGS_TO relationships
        belongs_to_calls = mock_session.run.call_args_list[6:12]
        for call in belongs_to_calls:
            query = call[0][0]
            assert "MATCH (t:Tag {id: $tag, owner_id: $owner_id})" in query
            assert "MATCH (c:Category {id: $category, owner_id: $owner_id})" in query
            assert "MERGE (t)-[b:BELONGS_TO]->(c)" in query
            assert "ON CREATE SET b.weight = 1" in query
            assert "ON MATCH SET b.weight = b.weight + 1" in query

        # Verify RELATED_TO relationships
        related_to_calls = mock_session.run.call_args_list[12:15]
        for call in related_to_calls:
            query = call[0][0]
            assert "MATCH (t1:Tag {id: $tag1, owner_id: $owner_id})" in query
            assert "MATCH (t2:Tag {id: $tag2, owner_id: $owner_id})" in query
            assert "MERGE (t1)-[r:RELATED_TO]-(t2)" in query


@pytest.mark.asyncio
async def test_update_graph_skips_empty_inputs(graph_service, mock_neo4j_driver):
    """Test that update_graph skips processing when inputs are empty or invalid."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        # Test with empty tags
        await graph_service.update_graph(
            owner_id=1, tags=[], top_level_categories=["Science & Technology"]
        )
        assert mock_session.run.call_count == 0

        # Test with empty categories
        await graph_service.update_graph(
            owner_id=1, tags=["python"], top_level_categories=[]
        )
        assert mock_session.run.call_count == 0

        # Test with None inputs
        await graph_service.update_graph(
            owner_id=1, tags=None, top_level_categories=None
        )
        assert mock_session.run.call_count == 0

        # Test with whitespace-only inputs
        await graph_service.update_graph(
            owner_id=1, tags=["", "  "], top_level_categories=["", "  "]
        )
        assert mock_session.run.call_count == 0


@pytest.mark.asyncio
async def test_update_graph_normalizes_inputs(graph_service, mock_neo4j_driver):
    """Test that update_graph normalizes tags and categories by stripping whitespace."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=1,
            tags=["  python  ", "machine-learning", "  ai  "],
            top_level_categories=["  Science & Technology  "],
        )

        # Verify normalized values were used in calls
        calls = mock_session.run.call_args_list

        # Check Category creation call
        category_call = calls[1]  # Second call after Root creation
        kwargs = category_call[1]
        assert kwargs["category"] == "Science & Technology"  # Stripped

        # Check Tag creation calls
        tag_creation_calls = calls[2:5]  # Next 3 calls
        tag_names = []
        for call in tag_creation_calls:
            kwargs = call[1]
            tag_names.append(kwargs["tag"])

        assert "python" in tag_names  # Stripped
        assert "machine-learning" in tag_names
        assert "ai" in tag_names  # Stripped
        assert "  python  " not in tag_names
        assert "  ai  " not in tag_names


@pytest.mark.asyncio
async def test_update_graph_with_single_tag_and_category(
    graph_service, mock_neo4j_driver
):
    """Test that update_graph works with minimum viable inputs."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=1, tags=["python"], top_level_categories=["Science & Technology"]
        )

        # Expected calls:
        # 1. Create Root node
        # 2. Create Category node
        # 3. Create Tag node
        # 4. Create BELONGS_TO relationship
        # No RELATED_TO relationships (only 1 tag)
        # Total: 4 calls
        assert mock_session.run.call_count == 4

        # Verify the BELONGS_TO relationship was created
        belongs_to_call = mock_session.run.call_args_list[3]
        query = belongs_to_call[0][0]
        assert "MERGE (t)-[b:BELONGS_TO]->(c)" in query
