"""Tests for worker embedding integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.resource import ProcessingStatus, Resource, ResourceStatus
from services.llm_processor import LLMResult
from workers.tasks import process_resource


@pytest.mark.asyncio
async def test_process_resource_embedding_success():
    """Test successful embedding generation during resource processing."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content for embedding"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING
    mock_resource.title = None
    mock_resource.summary = None
    mock_resource.tags = None
    mock_resource.top_level_categories = None
    mock_resource.fetch_tier = None

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test", "content"]
    mock_llm_result.top_level_categories = ["Science & Technology"]

    # Mock embedding generation
    mock_embedding = [0.1] * 2048

    with patch("workers.tasks.AsyncSessionLocal") as mock_session_factory:
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session.execute.return_value = mock_result

        # Mock categories query
        mock_categories_result = MagicMock()
        mock_categories_result.fetchall.return_value = [
            MagicMock(name="Science & Technology"),
            MagicMock(name="Programming"),
        ]

        # Setup session.execute to return different results based on call order
        mock_session.execute.side_effect = [
            mock_result,  # Resource query
            mock_categories_result,  # Categories query
            None,  # Embedding upsert query
        ]

        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.get_user_tags = AsyncMock(return_value=["existing", "tag"])
            mock_graph_service.update_graph = AsyncMock()
            mock_graph_service.update_from_resource = AsyncMock()

            with patch("workers.tasks.llm_processor_service") as mock_llm_service:
                mock_llm_service.process_content = AsyncMock(return_value=mock_llm_result)

                with patch("workers.tasks.embedding_service") as mock_embedding_service:
                    mock_embedding_service.build_embedding_text.return_value = "Test Title Test summary test content Science & Technology"
                    mock_embedding_service.generate_embedding = AsyncMock(return_value=mock_embedding)
                    mock_embedding_service.upsert_resource_embedding = AsyncMock()

                    # Execute
                    result = await process_resource({}, "123")

                    # Verify embedding service calls
                    mock_embedding_service.build_embedding_text.assert_called_once_with(mock_resource)
                    mock_embedding_service.generate_embedding.assert_called_once_with(
                        "Test Title Test summary test content Science & Technology"
                    )
                    mock_embedding_service.upsert_resource_embedding.assert_called_once_with(
                        mock_session, 123, mock_embedding
                    )

                    # Verify successful result
                    assert result["status"] == "ready"
                    assert "embedding_generation" in result["stages_completed"]


@pytest.mark.asyncio
async def test_process_resource_embedding_failure_graceful():
    """Test that embedding failure doesn't break the entire pipeline."""
    # Mock resource
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = "Test content"
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING
    mock_resource.title = None
    mock_resource.summary = None
    mock_resource.tags = None
    mock_resource.top_level_categories = None
    mock_resource.fetch_tier = None

    # Mock successful LLM processing
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = "Test Title"
    mock_llm_result.summary = "Test summary"
    mock_llm_result.tags = ["test"]
    mock_llm_result.top_level_categories = ["Science & Technology"]

    with patch("workers.tasks.AsyncSessionLocal") as mock_session_factory:
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session.execute.return_value = mock_result

        # Mock categories query
        mock_categories_result = MagicMock()
        mock_categories_result.fetchall.return_value = [
            MagicMock(name="Science & Technology"),
        ]

        # Setup session.execute to return different results
        mock_session.execute.side_effect = [
            mock_result,  # Resource query
            mock_categories_result,  # Categories query
        ]

        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.get_user_tags = AsyncMock(return_value=[])
            mock_graph_service.update_graph = AsyncMock()
            mock_graph_service.update_from_resource = AsyncMock()

            with patch("workers.tasks.llm_processor_service") as mock_llm_service:
                mock_llm_service.process_content = AsyncMock(return_value=mock_llm_result)

                with patch("workers.tasks.embedding_service") as mock_embedding_service:
                    # Mock embedding failure
                    mock_embedding_service.build_embedding_text.return_value = "Test Title Test summary test Science & Technology"
                    mock_embedding_service.generate_embedding = AsyncMock(side_effect=Exception("API Error"))

                    # Execute - should not raise exception
                    result = await process_resource({}, "123")

                    # Verify embedding service was called but failed gracefully
                    mock_embedding_service.build_embedding_text.assert_called_once_with(mock_resource)
                    mock_embedding_service.generate_embedding.assert_called_once()

                    # Resource should still be processed successfully
                    assert result["status"] == "ready"
                    assert "embedding_generation" in result["stages_completed"]


@pytest.mark.asyncio
async def test_process_resource_empty_embedding_text():
    """Test worker behavior when resource has no content for embedding."""
    # Mock resource with no searchable content
    mock_resource = MagicMock(spec=Resource)
    mock_resource.id = 123
    mock_resource.owner_id = 1
    mock_resource.content_type = "text"
    mock_resource.original_content = ""
    mock_resource.status = ResourceStatus.PENDING
    mock_resource.processing_status = ProcessingStatus.PENDING
    mock_resource.title = None
    mock_resource.summary = None
    mock_resource.tags = None
    mock_resource.top_level_categories = None
    mock_resource.fetch_tier = None

    # Mock LLM processing that returns empty/None fields
    mock_llm_result = MagicMock(spec=LLMResult)
    mock_llm_result.success = True
    mock_llm_result.title = None
    mock_llm_result.summary = None
    mock_llm_result.tags = []
    mock_llm_result.top_level_categories = []

    with patch("workers.tasks.AsyncSessionLocal") as mock_session_factory:
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session.execute.return_value = mock_result

        # Mock categories query
        mock_categories_result = MagicMock()
        mock_categories_result.fetchall.return_value = []
        mock_session.execute.side_effect = [
            mock_result,  # Resource query
            mock_categories_result,  # Categories query
        ]

        with patch("workers.tasks.graph_service") as mock_graph_service:
            mock_graph_service.get_user_tags = AsyncMock(return_value=[])

            with patch("workers.tasks.llm_processor_service") as mock_llm_service:
                mock_llm_service.process_content = AsyncMock(return_value=mock_llm_result)

                with patch("workers.tasks.embedding_service") as mock_embedding_service:
                    mock_embedding_service.build_embedding_text.return_value = ""  # Empty text
                    mock_embedding_service.generate_embedding = AsyncMock()
                    mock_embedding_service.upsert_resource_embedding = AsyncMock()

                    # Execute
                    result = await process_resource({}, "123")

                    # Verify embedding service was called but no embedding generated
                    mock_embedding_service.build_embedding_text.assert_called_once_with(mock_resource)
                    mock_embedding_service.generate_embedding.assert_not_called()
                    mock_embedding_service.upsert_resource_embedding.assert_not_called()

                    # Resource should still be processed successfully
                    assert result["status"] == "ready"
                    assert "embedding_generation" in result["stages_completed"]