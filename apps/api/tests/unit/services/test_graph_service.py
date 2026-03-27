"""Unit tests for GraphService hierarchical functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from services.graph_service import GraphService


@pytest.fixture
def graph_service():
    """Create a GraphService instance for testing."""
    return GraphService()


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for unit testing."""
    import contextlib

    mock_driver = AsyncMock()
    mock_session = AsyncMock()

    # Mock the driver.get_session() to return an async context manager
    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.get_session = lambda: mock_session_context()
    return mock_driver, mock_session


@pytest.mark.asyncio
async def test_update_graph_creates_hierarchy(graph_service, mock_neo4j_driver):
    """Test that update_graph creates Root -> Category -> Tag hierarchy."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=123,
            tags=["machine-learning", "python", "ai"],
            top_level_categories=["Science & Technology", "Education & Knowledge"],
        )

    # Verify session was used
    mock_driver.get_session.assert_called_once()

    # Verify all expected queries were called
    calls = mock_session.run.call_args_list
    assert len(calls) >= 7  # Root + 2 Categories + 3 Tags + 6 BELONGS_TO + RELATED_TO

    # Check Root node creation
    root_query = calls[0][0][0]
    assert "MERGE (r:Root {owner_id: $owner_id})" in root_query
    assert "node_type = 'root'" in root_query

    # Check Category node creation
    category_queries = [call[0][0] for call in calls[1:3]]
    for query in category_queries:
        assert "MERGE (c:Category {id: $category, owner_id: $owner_id})" in query
        assert "node_type = 'category'" in query
        assert "CHILD_OF" in query

    # Check Tag node creation
    tag_queries = [call[0][0] for call in calls[3:6]]
    for query in tag_queries:
        assert "MERGE (t:Tag {id: $tag, owner_id: $owner_id})" in query
        assert "node_type = 'topic'" in query


@pytest.mark.asyncio
async def test_update_graph_creates_belongs_to_relationships(
    graph_service, mock_neo4j_driver
):
    """Test that BELONGS_TO relationships are created between Tags and Categories."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=123,
            tags=["python", "ai"],
            top_level_categories=["Science & Technology"],
        )

    # Check for BELONGS_TO relationship creation
    calls = mock_session.run.call_args_list
    belongs_to_queries = [call[0][0] for call in calls if "BELONGS_TO" in call[0][0]]

    # Should have 2 BELONGS_TO queries (python->category, ai->category)
    tag_to_category_queries = [
        query
        for query in belongs_to_queries
        if "MERGE (t)-[b:BELONGS_TO]->(c)" in query
    ]
    assert len(tag_to_category_queries) == 2


@pytest.mark.asyncio
async def test_update_graph_creates_related_to_relationships(
    graph_service, mock_neo4j_driver
):
    """Test that RELATED_TO relationships are created between co-occurring Tags."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        await graph_service.update_graph(
            owner_id=123,
            tags=["python", "ai", "machine-learning"],
            top_level_categories=["Science & Technology"],
        )

    # Check for RELATED_TO relationship creation
    calls = mock_session.run.call_args_list
    related_to_queries = [call[0][0] for call in calls if "RELATED_TO" in call[0][0]]

    # Should have 3 RELATED_TO queries for 3 tags: (python,ai), (python,ml), (ai,ml)
    tag_to_tag_queries = [
        query
        for query in related_to_queries
        if "MERGE (t1)-[r:RELATED_TO]-(t2)" in query
    ]
    assert len(tag_to_tag_queries) == 3


@pytest.mark.asyncio
async def test_update_graph_skips_empty_inputs(graph_service, mock_neo4j_driver):
    """Test that update_graph skips processing when inputs are empty."""
    mock_driver, mock_session = mock_neo4j_driver

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        # Test with empty tags
        await graph_service.update_graph(
            owner_id=123,
            tags=[],
            top_level_categories=["Science & Technology"],
        )

        # Test with empty categories
        await graph_service.update_graph(
            owner_id=123,
            tags=["python"],
            top_level_categories=[],
        )

    # Should not have called any Neo4j operations
    mock_driver.get_session.assert_not_called()


@pytest.mark.asyncio
async def test_get_graph_returns_hierarchical_structure(
    graph_service, mock_neo4j_driver
):
    """Test that get_graph returns hierarchical structure with node_type."""
    mock_driver, mock_session = mock_neo4j_driver

    # Mock the result for default view (Root + Categories)
    mock_result = AsyncMock()
    mock_session.run.return_value = mock_result

    # Mock records for Root and Categories
    mock_records = [
        {
            "r": {"owner_id": "123", "name": "My Learning Space"},
            "c": {"id": "Science & Technology", "name": "Science & Technology"},
        },
        {
            "r": {"owner_id": "123", "name": "My Learning Space"},
            "c": {"id": "Education & Knowledge", "name": "Education & Knowledge"},
        },
    ]

    async def mock_async_iter():
        for record in mock_records:
            yield record

    mock_result.__aiter__ = mock_async_iter

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        result = await graph_service.get_graph(owner_id=123, root=None)

    # Verify structure
    assert "nodes" in result
    assert "edges" in result

    nodes = result["nodes"]
    assert len(nodes) == 3  # Root + 2 Categories

    # Check Root node
    root_nodes = [n for n in nodes if n.get("node_type") == "root"]
    assert len(root_nodes) == 1
    assert root_nodes[0]["id"] == "My Learning Space"
    assert root_nodes[0]["label"] == "My Learning Space"

    # Check Category nodes
    category_nodes = [n for n in nodes if n.get("node_type") == "category"]
    assert len(category_nodes) == 2
    category_ids = {n["id"] for n in category_nodes}
    assert category_ids == {"Science & Technology", "Education & Knowledge"}


@pytest.mark.asyncio
async def test_get_neighbors_returns_hierarchical_neighbors(
    graph_service, mock_neo4j_driver
):
    """Test that get_neighbors returns appropriate neighbors based on node type."""
    mock_driver, mock_session = mock_neo4j_driver

    # Mock the result for expanding a category
    mock_result = AsyncMock()
    mock_session.run.return_value = mock_result

    # Mock records for Category -> Tag expansion
    mock_records = [
        {
            "root_node": {
                "id": "Science & Technology",
                "name": "Science & Technology",
                "node_type": "category",
            },
            "child_tag": {
                "id": "python",
                "name": "python",
                "node_type": "topic",
            },
            "related_tag": None,
            "parent_cat": None,
        },
        {
            "root_node": {
                "id": "Science & Technology",
                "name": "Science & Technology",
                "node_type": "category",
            },
            "child_tag": {
                "id": "ai",
                "name": "ai",
                "node_type": "topic",
            },
            "related_tag": None,
            "parent_cat": None,
        },
    ]

    async def mock_async_iter():
        for record in mock_records:
            yield record

    mock_result.__aiter__ = mock_async_iter

    with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
        result = await graph_service.get_neighbors(
            owner_id=123, node_id="Science & Technology", direction="out"
        )

    # Verify structure
    assert "nodes" in result
    assert "edges" in result

    nodes = result["nodes"]
    assert len(nodes) == 2  # python + ai

    # All returned nodes should be topics (child tags)
    for node in nodes:
        assert node["node_type"] == "topic"
        assert node["level"] == "child"
        assert node["resource_count"] == 1

    # Check edges connect category to its child tags
    edges = result["edges"]
    assert len(edges) == 2
    for edge in edges:
        assert edge["target"] == "Science & Technology"  # BELONGS_TO points to category
