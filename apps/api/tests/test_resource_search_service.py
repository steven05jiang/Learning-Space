"""
Tests for ResourceSearchService.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

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
        session=mock_session,
        owner_id=uuid4(),
        query="",
        tag=None,
        limit=20,
        offset=0
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
        offset=0
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
    assert "tags ?? :tag" in sql_text  # JSONB ? operator (doubled for SQLAlchemy)
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

    result = await search_service._full_text_search(
        session=mock_session,
        owner_id=uuid4(),
        query="test",
        tag=None,
        limit=2,
        offset=0,
    )

    assert isinstance(result, SearchResult)
    assert len(result.resources) == 2
    assert result.total == 25  # Should reflect the total count, not just returned items
    assert result.resources[0].title == "Resource 1"
    assert result.resources[1].title == "Resource 2"


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search behavior when no results are found."""
    search_service = ResourceSearchService()

    # Mock session with empty result
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    result = await search_service._full_text_search(
        session=mock_session,
        owner_id=uuid4(),
        query="nonexistent",
        tag=None,
        limit=20,
        offset=0,
    )

    assert isinstance(result, SearchResult)
    assert result.resources == []
    assert result.total == 0
