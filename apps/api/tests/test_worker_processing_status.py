"""Tests for worker processing status state machine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.resource import ProcessingStatus, Resource, ResourceStatus
from services.llm_processor import LLMResult
from services.tiered_url_fetcher import TieredFetchResult
from workers.tasks import process_resource


@pytest.mark.asyncio
async def test_process_resource_start_to_processing_transition():
    """Test that worker sets processing_status to PROCESSING at start."""
    # Mock resource starting in PENDING state
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING

    # Track status changes
    processing_status_history = []

    def track_processing_status_changes(value):
        processing_status_history.append(value)

    # Mock setting processing_status to track changes
    default_status = ProcessingStatus.PENDING

    def get_status(self):
        if processing_status_history:
            return processing_status_history[-1]
        return default_status

    type(mock_resource).processing_status = property(
        get_status, lambda self, value: track_processing_status_changes(value)
    )

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test", "content"]
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

        with patch("workers.tasks.llm_processor_service") as mock_llm:
            mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

            with patch("workers.tasks.graph_service") as mock_graph:
                mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                await process_resource({}, "123")

                # Verify state transitions happened in correct order
                assert ProcessingStatus.PROCESSING in processing_status_history
                assert ProcessingStatus.SUCCESS in processing_status_history

                # Verify PROCESSING was set before SUCCESS
                processing_idx = processing_status_history.index(
                    ProcessingStatus.PROCESSING
                )
                success_idx = processing_status_history.index(ProcessingStatus.SUCCESS)
                assert processing_idx < success_idx


@pytest.mark.asyncio
async def test_process_resource_success_path():
    """Test that worker sets processing_status to SUCCESS on successful completion."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test", "content"]
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

        with patch("workers.tasks.llm_processor_service") as mock_llm:
            mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

            with patch("workers.tasks.graph_service") as mock_graph:
                mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                result = await process_resource({}, "123")

                # Verify final processing_status is SUCCESS
                assert mock_resource.processing_status == ProcessingStatus.SUCCESS
                assert mock_resource.status == ResourceStatus.READY
                assert result["status"] == "ready"


@pytest.mark.asyncio
async def test_process_resource_failure_path_fetch_error():
    """Test that worker sets processing_status to FAILED on fetch error."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "url"
    mock_resource.original_content = "https://example.com"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING

    # Mock failed fetch
    mock_fetch_result = TieredFetchResult(
        success=False,
        error_type="FETCH_ERROR",
        error_message="Could not reach URL",
        fetch_tier="http",
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

            # Verify processing_status is FAILED
            assert mock_resource.processing_status == ProcessingStatus.FAILED
            assert mock_resource.status == ResourceStatus.FAILED
            assert result["status"] == "failed"
            assert result["stage"] == "content_fetch"


@pytest.mark.asyncio
async def test_process_resource_failure_path_llm_error():
    """Test that worker sets processing_status to FAILED on LLM error."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING

    # Mock failed LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = False
    mock_llm_result.error_message = "LLM service unavailable"

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

        with patch("workers.tasks.llm_processor_service") as mock_llm:
            mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

            with patch("workers.tasks.graph_service") as mock_graph:
                mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                result = await process_resource({}, "123")

            # Verify processing_status is FAILED
            assert mock_resource.processing_status == ProcessingStatus.FAILED
            assert mock_resource.status == ResourceStatus.FAILED
            assert result["status"] == "failed"
            assert result["stage"] == "llm_processing"


@pytest.mark.asyncio
async def test_process_resource_skip_if_already_success():
    """Test that worker skips processing if resource is already in SUCCESS state."""
    # Mock resource already in SUCCESS state
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.processing_status = ProcessingStatus.SUCCESS

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session_instance.execute.return_value = mock_result

        result = await process_resource({}, "123")

        # Verify task was skipped
        assert result["status"] == "skipped"
        assert result["reason"] == "Already in terminal state: success"
        assert result["processing_status"] == "success"

        # Verify no processing steps were taken (no status changes)
        assert mock_resource.processing_status == ProcessingStatus.SUCCESS


@pytest.mark.asyncio
async def test_process_resource_skip_if_already_failed():
    """Test that worker skips processing if resource is already in FAILED state."""
    # Mock resource already in FAILED state
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.processing_status = ProcessingStatus.FAILED

    with patch("workers.tasks.AsyncSessionLocal") as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session_instance.execute.return_value = mock_result

        result = await process_resource({}, "123")

        # Verify task was skipped
        assert result["status"] == "skipped"
        assert result["reason"] == "Already in terminal state: failed"
        assert result["processing_status"] == "failed"

        # Verify no processing steps were taken (no status changes)
        assert mock_resource.processing_status == ProcessingStatus.FAILED


@pytest.mark.asyncio
async def test_process_resource_processing_state_allows_retry():
    """Test worker processes resource if in PROCESSING state (allows retry)."""
    # Mock resource in PROCESSING state (could be stale/stuck)
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PROCESSING
    mock_resource.processing_status = ProcessingStatus.PROCESSING

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test", "content"]
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

        with patch("workers.tasks.llm_processor_service") as mock_llm:
            mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

            with patch("workers.tasks.graph_service") as mock_graph:
                mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                result = await process_resource({}, "123")

                # Verify task was processed (not skipped)
                assert result["status"] == "ready"
                assert mock_resource.processing_status == ProcessingStatus.SUCCESS


@pytest.mark.asyncio
async def test_process_resource_pending_state_allows_processing():
    """Test that worker processes resource if it's in PENDING state."""
    # Mock resource in PENDING state (normal case)
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test", "content"]
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

        with patch("workers.tasks.llm_processor_service") as mock_llm:
            mock_llm.process_content = AsyncMock(return_value=mock_llm_result)

            with patch("workers.tasks.graph_service") as mock_graph:
                mock_graph.get_user_tags = AsyncMock(return_value=["existing"])
                result = await process_resource({}, "123")

                # Verify task was processed (not skipped)
                assert result["status"] == "ready"
                assert mock_resource.processing_status == ProcessingStatus.SUCCESS
