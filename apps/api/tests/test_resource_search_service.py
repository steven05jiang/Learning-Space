"""
Tests for ResourceSearchService.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from services.resource_search_service import (
    AgentResourceResult,
    ResourceSearchItem,
    ResourceSearchService,
    SearchResult,
)


@pytest.fixture
def search_service():
    """Create a fresh ResourceSearchService instance for testing."""
    return ResourceSearchService()


@pytest.fixture
def sample_search_result():
    """Create sample search result data for testing."""
    resource_id = uuid4()
    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()

    # Mock SQLAlchemy row
    mock_row = MagicMock()
    mock_row.id = resource_id
    mock_row.title = "Building AI Agents with LangGraph"
    mock_row.summary = "A guide to building stateful multi-step AI agents."
    mock_row.tags = ["LangGraph", "AI Agents", "LLM Tools"]
    mock_row.top_level_categories = ["Science & Technology"]
    mock_row.original_content = "https://example.com/langraph-agents"
    mock_row.content_type = "url"
    mock_row.status = "READY"
    mock_row.created_at = created_at
    mock_row.updated_at = updated_at
    mock_row.rank = 0.842
    mock_row.total_count = 1

    item = ResourceSearchItem.from_row(mock_row)
    return mock_row, item


@pytest.mark.asyncio
async def test_search_empty_query_returns_empty_result(search_service):
    """Test that empty or whitespace-only queries return empty results."""
    mock_session = AsyncMock()

    result = await search_service.search(
        session=mock_session, owner_id=uuid4(), query="", tag=None, limit=20, offset=0
    )

    assert isinstance(result, SearchResult)
    assert result.resources == []
    assert result.total == 0

    # Test whitespace-only query
    result = await search_service.search(
        session=mock_session,
        owner_id=uuid4(),
        query="   ",
        tag=None,
        limit=20,
        offset=0,
    )

    assert result.resources == []
    assert result.total == 0


def test_resource_search_item_from_row(sample_search_result):
    """Test ResourceSearchItem.from_row() correctly parses SQLAlchemy row."""
    mock_row, item = sample_search_result

    assert item.id == str(mock_row.id)
    assert item.title == "Building AI Agents with LangGraph"
    assert item.summary == "A guide to building stateful multi-step AI agents."
    assert item.tags == ["LangGraph", "AI Agents", "LLM Tools"]
    assert item.top_level_categories == ["Science & Technology"]
    assert item.original_content == "https://example.com/langraph-agents"
    assert item.content_type == "url"
    assert item.status == "READY"
    assert item.rank == 0.842


def test_resource_search_item_from_row_handles_nulls():
    """Test ResourceSearchItem.from_row() handles None values correctly."""
    mock_row = MagicMock()
    mock_row.id = uuid4()
    mock_row.title = None
    mock_row.summary = None
    mock_row.tags = None
    mock_row.top_level_categories = None
    mock_row.original_content = "Some text content"
    mock_row.content_type = "text"
    mock_row.status = "READY"
    mock_row.created_at = datetime.utcnow()
    mock_row.updated_at = datetime.utcnow()
    mock_row.rank = 0.5

    item = ResourceSearchItem.from_row(mock_row)

    assert item.title is None
    assert item.summary is None
    assert item.tags == []  # None becomes empty list
    assert item.top_level_categories == []  # None becomes empty list
    assert item.content_type == "text"
    assert item.rank == 0.5


def test_agent_resource_result_from_item_url_resource(sample_search_result):
    """Test AgentResourceResult.from_item() for URL resources."""
    _, item = sample_search_result

    agent_result = AgentResourceResult.from_item(item)

    assert agent_result.id == str(item.id)
    assert agent_result.title == "Building AI Agents with LangGraph"
    assert agent_result.summary == "A guide to building stateful multi-step AI agents."
    assert agent_result.tags == ["LangGraph", "AI Agents", "LLM Tools"]
    assert agent_result.top_level_categories == ["Science & Technology"]
    assert agent_result.url == "https://example.com/langraph-agents"


def test_agent_resource_result_from_item_text_resource():
    """Test AgentResourceResult.from_item() for text resources (url should be None)."""
    item = ResourceSearchItem(
        id=uuid4(),
        title="Python Tutorial",
        summary="A quick Python guide",
        tags=["Python", "Tutorial"],
        top_level_categories=["Technology"],
        original_content="def hello(): print('Hello World')",
        content_type="text",  # text resource
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.9,
    )

    agent_result = AgentResourceResult.from_item(item)

    assert agent_result.url is None  # Should be None for text resources
    assert agent_result.title == "Python Tutorial"


def test_agent_resource_result_handles_none_values():
    """Test AgentResourceResult.from_item() handles None title/summary gracefully."""
    item = ResourceSearchItem(
        id=uuid4(),
        title=None,
        summary=None,
        tags=["tag1"],
        top_level_categories=["category1"],
        original_content="https://example.com",
        content_type="url",
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.5,
    )

    agent_result = AgentResourceResult.from_item(item)

    assert agent_result.title == ""  # None becomes empty string
    assert agent_result.summary == ""  # None becomes empty string


@pytest.mark.asyncio
async def test_full_text_search_query_structure():
    """Test that _full_text_search() constructs the correct SQL query."""
    search_service = ResourceSearchService()

    # Mock session and execute
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    await search_service._full_text_search(
        session=mock_session,
        owner_id=uuid4(),
        query="langraph agents",
        tag="AI",
        limit=10,
        offset=0,
    )

    # Verify execute was called with correct parameters
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args

    # Check that SQL text contains expected elements
    sql_text = str(call_args[0][0])
    assert "to_tsvector" in sql_text
    assert "plainto_tsquery" in sql_text
    assert "ts_rank" in sql_text
    assert "COUNT(*) OVER()" in sql_text
    assert "status = 'READY'" in sql_text
    assert "jsonb_exists(tags, :tag)" in sql_text  # JSONB existence check via function
    assert "ORDER BY rank DESC" in sql_text

    # Check parameters
    params = call_args[0][1]
    assert "query" in params
    assert "owner_id" in params
    assert "tag" in params
    assert "limit" in params
    assert "offset" in params


@pytest.mark.asyncio
async def test_search_result_pagination():
    """Test that SearchResult correctly handles pagination data."""
    search_service = ResourceSearchService()

    # Create mock rows with total_count
    mock_row1 = MagicMock()
    mock_row1.id = uuid4()
    mock_row1.title = "Resource 1"
    mock_row1.summary = "Summary 1"
    mock_row1.tags = []
    mock_row1.top_level_categories = []
    mock_row1.original_content = "Content 1"
    mock_row1.content_type = "text"
    mock_row1.status = "READY"
    mock_row1.created_at = datetime.utcnow()
    mock_row1.updated_at = datetime.utcnow()
    mock_row1.rank = 0.9
    mock_row1.total_count = 25  # Total of 25 results

    mock_row2 = MagicMock()
    mock_row2.id = uuid4()
    mock_row2.title = "Resource 2"
    mock_row2.summary = "Summary 2"
    mock_row2.tags = []
    mock_row2.top_level_categories = []
    mock_row2.original_content = "Content 2"
    mock_row2.content_type = "text"
    mock_row2.status = "READY"
    mock_row2.created_at = datetime.utcnow()
    mock_row2.updated_at = datetime.utcnow()
    mock_row2.rank = 0.8
    mock_row2.total_count = 25  # Same total

    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row1, mock_row2]
    mock_session.execute.return_value = mock_result

    items, total = await search_service._full_text_search(
        session=mock_session,
        owner_id=uuid4(),
        query="test",
        tag=None,
        limit=2,
        offset=0,
    )

    assert isinstance(items, list)
    assert len(items) == 2
    assert total == 25  # Should reflect the total count, not just returned items
    assert items[0].title == "Resource 1"
    assert items[1].title == "Resource 2"


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search behavior when no results are found."""
    search_service = ResourceSearchService()

    # Mock session with empty result
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    items, total = await search_service._full_text_search(
        session=mock_session,
        owner_id=uuid4(),
        query="nonexistent",
        tag=None,
        limit=20,
        offset=0,
    )

    assert isinstance(items, list)
    assert items == []
    assert total == 0


# ========================== Hybrid Search Tests ==========================


@pytest.mark.asyncio
async def test_search_mode_keyword_uses_full_text_search(search_service):
    """Test that SEARCH_MODE=keyword uses full-text search (default behavior)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('core.config.settings.search_mode', 'keyword'):
        result = await search_service.search(
            session=mock_session,
            owner_id=123,
            query="test query",
            tag=None,
            limit=20,
            offset=0,
        )

    assert isinstance(result, SearchResult)
    assert result.resources == []
    assert result.total == 0
    # Verify that only execute was called (full-text search), not embedding service
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_mode_hybrid_calls_embedding_service():
    """Test that SEARCH_MODE=hybrid attempts to use embedding service."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()

    # Mock full-text search response
    mock_ft_row = MagicMock()
    mock_ft_row.id = "ft-resource-1"
    mock_ft_row.title = "Full Text Result"
    mock_ft_row.summary = "A full text result"
    mock_ft_row.tags = ["tag1"]
    mock_ft_row.top_level_categories = ["category1"]
    mock_ft_row.original_content = "content"
    mock_ft_row.content_type = "text"
    mock_ft_row.status = "READY"
    mock_ft_row.created_at = datetime.utcnow()
    mock_ft_row.updated_at = datetime.utcnow()
    mock_ft_row.rank = 0.8
    mock_ft_row.total_count = 1

    # Mock vector search response
    mock_vec_row = MagicMock()
    mock_vec_row.id = "vec-resource-1"
    mock_vec_row.title = "Vector Result"
    mock_vec_row.summary = "A vector result"
    mock_vec_row.tags = ["tag2"]
    mock_vec_row.top_level_categories = ["category2"]
    mock_vec_row.original_content = "content2"
    mock_vec_row.content_type = "text"
    mock_vec_row.status = "READY"
    mock_vec_row.created_at = datetime.utcnow()
    mock_vec_row.updated_at = datetime.utcnow()
    mock_vec_row.similarity = 0.9

    # Mock database calls
    mock_result_ft = MagicMock()
    mock_result_ft.fetchall.return_value = [mock_ft_row]
    mock_result_vec = MagicMock()
    mock_result_vec.fetchall.return_value = [mock_vec_row]

    # Set up session.execute to return different results based on SQL
    async def mock_execute(sql, params):
        if "ts_rank" in str(sql):
            return mock_result_ft
        elif "embedding <=> " in str(sql):
            return mock_result_vec
        else:
            return MagicMock()

    mock_session.execute.side_effect = mock_execute

    # Mock embedding service
    with patch('core.config.settings.search_mode', 'hybrid'), \
         patch('services.resource_search_service.embedding_service') as mock_embedding:

        async def mock_generate_embedding(text):
            return [0.1] * 2048

        mock_embedding.generate_embedding = AsyncMock(side_effect=mock_generate_embedding)

        result = await search_service.search(
            session=mock_session,
            owner_id=123,
            query="test query",
            tag=None,
            limit=20,
            offset=0,
        )

        # Verify embedding service was called
        mock_embedding.generate_embedding.assert_called_once_with("test query")

    assert isinstance(result, SearchResult)
    assert len(result.resources) == 2  # Should have merged results
    assert result.total == 2


@pytest.mark.asyncio
async def test_hybrid_search_fallback_on_embedding_failure():
    """Test that hybrid search falls back to full-text when embedding fails."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()

    # Mock full-text search response
    mock_row = MagicMock()
    mock_row.id = "resource-1"
    mock_row.title = "Fallback Result"
    mock_row.summary = "A fallback result"
    mock_row.tags = ["tag1"]
    mock_row.top_level_categories = ["category1"]
    mock_row.original_content = "content"
    mock_row.content_type = "text"
    mock_row.status = "READY"
    mock_row.created_at = datetime.utcnow()
    mock_row.updated_at = datetime.utcnow()
    mock_row.rank = 0.8
    mock_row.total_count = 1

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    # Mock embedding service to fail
    with patch('core.config.settings.search_mode', 'hybrid'), \
         patch('services.resource_search_service.embedding_service') as mock_embedding:
        mock_embedding.generate_embedding.return_value = None  # Simulate failure

        result = await search_service.search(
            session=mock_session,
            owner_id=123,
            query="test query",
            tag=None,
            limit=20,
            offset=0,
        )

    assert isinstance(result, SearchResult)
    assert len(result.resources) == 1
    assert result.resources[0].title == "Fallback Result"
    assert result.total == 1


@pytest.mark.asyncio
async def test_hybrid_search_fallback_on_exception():
    """Test that hybrid search falls back to full-text when any exception occurs."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()

    # Mock full-text search response (for fallback)
    mock_row = MagicMock()
    mock_row.id = "resource-1"
    mock_row.title = "Exception Fallback"
    mock_row.summary = "A fallback after exception"
    mock_row.tags = ["tag1"]
    mock_row.top_level_categories = ["category1"]
    mock_row.original_content = "content"
    mock_row.content_type = "text"
    mock_row.status = "READY"
    mock_row.created_at = datetime.utcnow()
    mock_row.updated_at = datetime.utcnow()
    mock_row.rank = 0.8
    mock_row.total_count = 1

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    # Mock embedding service to raise exception
    with patch('core.config.settings.search_mode', 'hybrid'), \
         patch('services.resource_search_service.embedding_service') as mock_embedding:
        mock_embedding.generate_embedding.side_effect = Exception("API timeout")

        result = await search_service.search(
            session=mock_session,
            owner_id=123,
            query="test query",
            tag=None,
            limit=20,
            offset=0,
        )

    assert isinstance(result, SearchResult)
    assert len(result.resources) == 1
    assert result.resources[0].title == "Exception Fallback"
    assert result.total == 1


@pytest.mark.asyncio
async def test_vector_search_query_structure():
    """Test that _vector_search() constructs the correct SQL query."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    query_embedding = [0.1] * 2048
    await search_service._vector_search(
        session=mock_session,
        owner_id=123,
        query_embedding=query_embedding,
        tag="test-tag",
        limit=10,
    )

    # Verify execute was called with correct SQL structure
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args

    # Check SQL contains vector search elements
    sql_text = str(call_args[0][0])
    assert "embedding <=> :query_embedding::vector" in sql_text
    assert "resource_embeddings re ON re.resource_id = r.id" in sql_text
    assert "1 - (re.embedding <=> :query_embedding::vector) AS similarity" in sql_text
    assert "ORDER BY re.embedding <=> :query_embedding::vector" in sql_text

    # Check parameters
    params = call_args[0][1]
    assert "query_embedding" in params
    assert "owner_id" in params
    assert "tag" in params
    assert "limit" in params
    assert params["query_embedding"] == query_embedding


@pytest.mark.asyncio
async def test_embed_helper_calls_embedding_service():
    """Test that _embed() helper correctly calls the embedding service."""
    search_service = ResourceSearchService()

    with patch('services.resource_search_service.embedding_service') as mock_embedding:
        async def mock_generate_embedding(text):
            return [0.1] * 2048

        mock_embedding.generate_embedding = AsyncMock(side_effect=mock_generate_embedding)

        result = await search_service._embed("test query")

        mock_embedding.generate_embedding.assert_called_once_with("test query")
        assert result == [0.1] * 2048


@pytest.mark.asyncio
async def test_rrf_merge_algorithm():
    """Test that RRF (Reciprocal Rank Fusion) algorithm is correctly implemented."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()

    # Create mock items for full-text search (item1 ranks higher)
    ft_item1 = ResourceSearchItem(
        id="resource-1",
        title="FT Result 1",
        summary="summary1",
        tags=[],
        top_level_categories=[],
        original_content="content1",
        content_type="text",
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.9,
    )

    ft_item2 = ResourceSearchItem(
        id="resource-2",
        title="FT Result 2",
        summary="summary2",
        tags=[],
        top_level_categories=[],
        original_content="content2",
        content_type="text",
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.8,
    )

    # Create mock items for vector search (item2 ranks higher)
    vec_item2 = ResourceSearchItem(
        id="resource-2",  # Same as ft_item2
        title="Vec Result 2",
        summary="summary2",
        tags=[],
        top_level_categories=[],
        original_content="content2",
        content_type="text",
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.95,
    )

    vec_item3 = ResourceSearchItem(
        id="resource-3",
        title="Vec Result 3",
        summary="summary3",
        tags=[],
        top_level_categories=[],
        original_content="content3",
        content_type="text",
        status="READY",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        rank=0.85,
    )

    # Mock the two search methods
    with patch.object(search_service, '_full_text_search') as mock_ft, \
         patch.object(search_service, '_embed') as mock_embed, \
         patch.object(search_service, '_vector_search') as mock_vec:

        mock_ft.return_value = ([ft_item1, ft_item2], 2)
        mock_embed.return_value = [0.1] * 2048
        mock_vec.return_value = [vec_item2, vec_item3]

        items, total = await search_service._hybrid_search(
            session=mock_session,
            owner_id=123,
            query="test",
            tag=None,
            limit=10,
            offset=0,
        )

        # Verify RRF scoring
        # resource-2 appears in both lists, so gets higher combined score
        # RRF formula: 1/(k + rank + 1) where k=60
        # resource-1: 1/(60+0+1) = 1/61 ≈ 0.016393
        # resource-2: 1/(60+1+1) + 1/(60+0+1) = 1/62 + 1/61 ≈ 0.032524
        # resource-3: 1/(60+1+1) = 1/62 ≈ 0.016129

        assert total == 3
        assert len(items) == 3

        # resource-2 should be first due to appearing in both results
        assert items[0].id == "resource-2"
        # Verify that rank was updated to RRF score
        assert items[0].rank > items[1].rank
        assert items[0].rank > items[2].rank


@pytest.mark.asyncio
async def test_hybrid_search_respects_pagination():
    """Test that hybrid search correctly applies offset and limit."""
    search_service = ResourceSearchService()
    mock_session = AsyncMock()

    # Create 5 mock items
    items = []
    for i in range(5):
        items.append(ResourceSearchItem(
            id=f"resource-{i}",
            title=f"Result {i}",
            summary=f"summary {i}",
            tags=[],
            top_level_categories=[],
            original_content=f"content {i}",
            content_type="text",
            status="READY",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rank=0.9 - i * 0.1,  # Decreasing scores
        ))

    # Mock the search methods
    with patch.object(search_service, '_full_text_search') as mock_ft, \
         patch.object(search_service, '_embed') as mock_embed, \
         patch.object(search_service, '_vector_search') as mock_vec:

        mock_ft.return_value = (items[:3], 3)  # First 3 items
        mock_embed.return_value = [0.1] * 2048
        mock_vec.return_value = items[2:]  # Last 3 items

        # Test pagination: offset=1, limit=2
        result_items, total = await search_service._hybrid_search(
            session=mock_session,
            owner_id=123,
            query="test",
            tag=None,
            limit=2,
            offset=1,
        )

        assert total == 5  # Total unique items
        assert len(result_items) == 2  # Limited to 2 items
        # Should skip first item (offset=1) and return next 2
