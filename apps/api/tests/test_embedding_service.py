"""Tests for embedding service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.resource import Resource
from services.embedding_service import embedding_service


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    def test_build_embedding_text_full_resource(self):
        """Test build_embedding_text with all fields populated."""
        resource = Resource(
            title="Test Title",
            summary="This is a test summary.",
            tags=["python", "testing"],
            top_level_categories=["Programming", "Technology"],
        )

        result = embedding_service.build_embedding_text(resource)
        expected = "Test Title This is a test summary. python testing Programming Technology"
        assert result == expected

    def test_build_embedding_text_partial_resource(self):
        """Test build_embedding_text with only some fields populated."""
        resource = Resource(
            title="Test Title",
            summary=None,
            tags=["python"],
            top_level_categories=None,
        )

        result = embedding_service.build_embedding_text(resource)
        expected = "Test Title python"
        assert result == expected

    def test_build_embedding_text_empty_resource(self):
        """Test build_embedding_text with no searchable fields."""
        resource = Resource(
            title=None,
            summary=None,
            tags=None,
            top_level_categories=None,
        )

        result = embedding_service.build_embedding_text(resource)
        assert result == ""

    def test_build_embedding_text_empty_arrays(self):
        """Test build_embedding_text with empty arrays."""
        resource = Resource(
            title="Test Title",
            summary="Summary",
            tags=[],
            top_level_categories=[],
        )

        result = embedding_service.build_embedding_text(resource)
        expected = "Test Title Summary"
        assert result == expected

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1] * 2048  # Exactly 2048 values

        with patch.object(embedding_service.client.embeddings, 'create', return_value=mock_response) as mock_create:
            result = await embedding_service.generate_embedding("test text")

        # Should return all 2048 values
        assert result == [0.1] * 2048
        mock_create.assert_called_once_with(
            model="Qwen/Qwen3-Embedding-4B",
            input="test text",
        )

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text."""
        result = await embedding_service.generate_embedding("")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_response_data(self):
        """Test embedding generation with empty response data."""
        mock_response = MagicMock()
        mock_response.data = []

        with patch.object(embedding_service.client.embeddings, 'create', return_value=mock_response) as mock_create:
            result = await embedding_service.generate_embedding("test text")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self):
        """Test embedding generation with API error."""
        with patch.object(embedding_service.client.embeddings, 'create', side_effect=Exception("API Error")) as mock_create:
            with pytest.raises(Exception, match="API Error"):
                await embedding_service.generate_embedding("test text")

    @pytest.mark.asyncio
    async def test_upsert_resource_embedding(self):
        """Test upsert_resource_embedding functionality."""
        mock_session = AsyncMock()
        embedding = [0.1, 0.2] * 1024  # 2048 values

        await embedding_service.upsert_resource_embedding(
            session=mock_session,
            resource_id=123,
            embedding=embedding,
            model="test-model",
        )

        # Verify SQL execution
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args

        # Check that the SQL contains INSERT ... ON CONFLICT
        sql_text = str(call_args[0][0])
        assert "INSERT INTO resource_embeddings" in sql_text
        assert "ON CONFLICT (resource_id)" in sql_text
        assert "DO UPDATE SET" in sql_text

        # Check parameters
        params = call_args[0][1]
        assert params["resource_id"] == 123
        assert params["embedding"] == embedding
        assert params["model"] == "test-model"

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_resource_embedding_default_model(self):
        """Test upsert_resource_embedding with default model."""
        mock_session = AsyncMock()
        embedding = [0.1] * 2048

        await embedding_service.upsert_resource_embedding(
            session=mock_session,
            resource_id=456,
            embedding=embedding,
        )

        # Verify default model is used
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["model"] == "Qwen/Qwen3-Embedding-4B"