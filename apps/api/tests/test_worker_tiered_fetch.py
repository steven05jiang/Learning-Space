"""Tests for worker task integration with tiered URL fetcher."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.resource import Resource, ResourceStatus
from services.tiered_url_fetcher import TieredFetchResult
from workers.tasks import process_resource


@pytest.mark.asyncio
async def test_process_resource_url_http_success():
    """Test resource processing with successful HTTP fetch."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "url"
    mock_resource.original_content = "https://example.com"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.fetch_tier = None
    mock_resource.fetch_error_type = None

    # Mock successful fetch
    mock_fetch_result = TieredFetchResult(
        success=True,
        content="Example website content",
        content_type="text/html",
        status_code=200,
        fetch_tier="http",
    )

    # Mock successful LLM processing
    mock_llm_result = MagicMock()
    mock_llm_result.success = True
    mock_llm_result.title = "Example Title"
    mock_llm_result.summary = "Example summary"
    mock_llm_result.tags = ["example", "test"]
    mock_llm_result.top_level_categories = ["Science & Technology"]

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock resource query result
        mock_resource_result = MagicMock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock categories query result
        mock_category_row = MagicMock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = MagicMock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session_instance.execute = AsyncMock(side_effect=mock_execute_side_effect)

        with patch("workers.tasks._fetcher") as mock_fetcher:
            mock_fetcher.fetch_url_content = AsyncMock(return_value=mock_fetch_result)

            with patch("workers.tasks.llm_processor_service") as mock_llm:
                mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

                with patch("workers.tasks.graph_service") as mock_graph:
                    mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                    result = await process_resource({}, "123")

                    # Verify fetch was called with correct parameters
                    mock_fetcher.fetch_url_content.assert_called_once_with(
                        "https://example.com", 1
                    )

                    # Verify resource was updated with fetch tier
                    assert mock_resource.fetch_tier == "http"
                    assert mock_resource.status == ResourceStatus.READY

                    # Verify result includes fetch tier
                    assert result["status"] == "ready"
                    assert result["fetch_tier"] == "http"


@pytest.mark.asyncio
async def test_process_resource_url_fetch_failure():
    """Test resource processing with fetch failure."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "url"
    mock_resource.original_content = "https://blocked.example.com"
    mock_resource.status = ResourceStatus.PENDING

    # Mock failed fetch
    mock_fetch_result = TieredFetchResult(
        success=False,
        error_type="BOT_BLOCKED",
        error_message="Page blocked automated access",
        fetch_tier="playwright",
    )

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session_instance.execute.return_value = mock_result

        with patch("workers.tasks._fetcher") as mock_fetcher:
            mock_fetcher.fetch_url_content = AsyncMock(return_value=mock_fetch_result)

            result = await process_resource({}, "123")

            # Verify resource was marked as failed
            assert mock_resource.status == ResourceStatus.FAILED
            assert mock_resource.fetch_error_type == "BOT_BLOCKED"
            assert "blocked automated access" in mock_resource.status_message

            # Verify result indicates failure
            assert result["status"] == "failed"
            assert result["fetch_error_type"] == "BOT_BLOCKED"
            assert result["fetch_tier"] == "playwright"


@pytest.mark.asyncio
async def test_process_resource_url_api_required():
    """Test resource processing with API-required domain."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "url"
    mock_resource.original_content = "https://twitter.com/example"
    mock_resource.status = ResourceStatus.PENDING

    # Mock API required fetch failure
    mock_fetch_result = TieredFetchResult(
        success=False,
        error_type="API_REQUIRED",
        error_message="Linked account required",
    )

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session_instance.execute.return_value = mock_result

        with patch("workers.tasks._fetcher") as mock_fetcher:
            mock_fetcher.fetch_url_content = AsyncMock(return_value=mock_fetch_result)

            result = await process_resource({}, "123")

            # Verify resource was marked as failed with API_REQUIRED
            assert mock_resource.status == ResourceStatus.FAILED
            assert mock_resource.fetch_error_type == "API_REQUIRED"
            assert "linked account" in mock_resource.status_message.lower()

            # Verify result indicates failure
            assert result["status"] == "failed"
            assert result["fetch_error_type"] == "API_REQUIRED"


@pytest.mark.asyncio
async def test_process_resource_text_content():
    """Test resource processing with text content (no fetch needed)."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "This is some text content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.fetch_tier = None

    # Mock successful LLM processing
    mock_llm_result = MagicMock()
    mock_llm_result.success = True
    mock_llm_result.title = "Text Title"
    mock_llm_result.summary = "Text summary"
    mock_llm_result.tags = ["text", "content"]
    mock_llm_result.top_level_categories = ["Science & Technology"]

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock resource query result
        mock_resource_result = MagicMock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock categories query result
        mock_category_row = MagicMock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = MagicMock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session_instance.execute = AsyncMock(side_effect=mock_execute_side_effect)

        with patch("workers.tasks._fetcher") as mock_fetcher:
            with patch("workers.tasks.llm_processor_service") as mock_llm:
                mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

                with patch("workers.tasks.graph_service") as mock_graph:
                    mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                    result = await process_resource({}, "123")

                    # Verify fetch was NOT called for text content
                    mock_fetcher.fetch_url_content.assert_not_called()

                    # Verify resource fetch_tier remains None for text content
                    assert mock_resource.fetch_tier is None
                    assert mock_resource.status == ResourceStatus.READY

                    # Verify result
                    assert result["status"] == "ready"
                    assert result["fetch_tier"] is None


def test_get_user_friendly_error_message():
    """Test error message mapping function."""
    from workers.tasks import _get_user_friendly_error_message

    # Test standard error types
    assert (
        "linked account"
        in _get_user_friendly_error_message("API_REQUIRED", "API error").lower()
    )

    assert (
        "not yet supported"
        in _get_user_friendly_error_message("NOT_SUPPORTED", "Not supported").lower()
    )

    assert (
        "blocked automated access"
        in _get_user_friendly_error_message("BOT_BLOCKED", "Bot blocked").lower()
    )

    assert (
        "could not reach"
        in _get_user_friendly_error_message("FETCH_ERROR", "Network error").lower()
    )

    # Test passthrough for validation errors
    assert (
        _get_user_friendly_error_message("validation_error", "URL cannot be empty")
        == "URL cannot be empty"
    )

    # Test fallback for unknown error types
    fallback_msg = _get_user_friendly_error_message(
        "unknown_error", "Some unknown error"
    )
    assert "Some unknown error" in fallback_msg
