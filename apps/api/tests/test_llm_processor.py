"""Tests for the LLM processor service."""

from unittest.mock import Mock, patch

import anthropic
import pytest

from services.llm_processor import LLMProcessorService, LLMResult


class TestLLMProcessorService:
    """Test cases for LLMProcessorService."""

    @pytest.fixture
    def processor_with_client(self):
        """Create an LLMProcessorService instance with mocked client."""
        with patch("services.llm_processor.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            processor = LLMProcessorService(api_key="test-api-key")
            processor.client = mock_client
            return processor

    @pytest.fixture
    def processor_no_client(self):
        """Create an LLMProcessorService instance without valid client."""
        return LLMProcessorService(api_key="test-anthropic-key-for-development")

    def test_initialization_with_valid_key(self):
        """Test initialization with valid API key."""
        with patch("services.llm_processor.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            processor = LLMProcessorService(api_key="test-key")

            assert processor.api_key == "test-key"
            assert processor.model == "claude-haiku-4-5-20251001"
            assert processor.client is not None

    def test_initialization_with_test_key(self):
        """Test initialization with development test key."""
        processor = LLMProcessorService(api_key="test-anthropic-key-for-development")

        assert processor.api_key == "test-anthropic-key-for-development"
        assert processor.client is None

    def test_initialization_without_key(self):
        """Test initialization without API key."""
        with patch("services.llm_processor.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            processor = LLMProcessorService()

            assert processor.client is None

    def test_initialization_with_exception(self):
        """Test initialization that fails to create client."""
        with patch(
            "services.llm_processor.Anthropic", side_effect=Exception("Invalid key")
        ):
            processor = LLMProcessorService(api_key="invalid-key")

            assert processor.client is None

    async def test_empty_content(self, processor_with_client):
        """Test processing empty content."""
        result = await processor_with_client.process_content("", "text/plain")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "Content cannot be empty"

    async def test_whitespace_only_content(self, processor_with_client):
        """Test processing whitespace-only content."""
        result = await processor_with_client.process_content("   ", "text/plain")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "Content cannot be empty"

    async def test_no_client_configured(self, processor_no_client):
        """Test processing when no client is configured."""
        result = await processor_no_client.process_content("Test content", "text/plain")

        assert result.success is False
        assert result.error_type == "configuration_error"
        assert "Anthropic API key not configured" in result.error_message

    async def test_successful_processing(self, processor_with_client):
        """Test successful content processing."""
        # Mock successful API response
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article Title",
            "summary": "This is a comprehensive summary of the test article content.",
            "tags": ["test", "article", "content", "sample"],
        }

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "This is test article content about various topics.", "text/plain"
        )

        assert result.success is True
        assert result.title == "Test Article Title"
        assert result.summary == (
            "This is a comprehensive summary of the test article content."
        )
        assert result.tags == ["test", "article", "content", "sample"]
        assert result.error_message is None

    async def test_empty_response(self, processor_with_client):
        """Test handling empty response from LLM."""
        mock_response = Mock()
        mock_response.content = []

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "api_error"
        assert result.error_message == "Empty response from LLM"

    async def test_no_tool_use_in_response(self, processor_with_client):
        """Test handling response without tool use."""
        mock_text_block = Mock()
        mock_text_block.type = "text"

        mock_response = Mock()
        mock_response.content = [mock_text_block]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "api_error"
        assert result.error_message == "No tool use found in LLM response"

    async def test_missing_title(self, processor_with_client):
        """Test handling missing title in response."""
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {"title": "", "summary": "Test summary", "tags": ["test"]}

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "extraction_error"
        assert result.error_message == "LLM failed to extract a valid title"

    async def test_missing_summary(self, processor_with_client):
        """Test handling missing summary in response."""
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {"title": "Test Title", "summary": "", "tags": ["test"]}

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "extraction_error"
        assert result.error_message == "LLM failed to extract a valid summary"

    async def test_tag_cleaning_and_limiting(self, processor_with_client):
        """Test tag cleaning and limiting functionality."""
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Title",
            "summary": "Test summary",
            "tags": [
                "Test Tag",  # Should become "test-tag"
                "python",
                "JAVASCRIPT",  # Should become "javascript"
                "machine learning",  # Should become "machine-learning"
                "python",  # Duplicate, should be removed
                "ai",
                "data science",  # Should become "data-science"
                "technology",
                "programming",
                "extra-tag",  # This makes 9 tags, should be limited to 8
            ],
        }

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is True
        assert len(result.tags) == 8  # Limited to 8 tags
        assert "test-tag" in result.tags
        assert "javascript" in result.tags
        assert "machine-learning" in result.tags
        assert "data-science" in result.tags
        # Should not have duplicates
        assert result.tags.count("python") == 1

    async def test_invalid_tags_format(self, processor_with_client):
        """Test handling invalid tags format."""
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Title",
            "summary": "Test summary",
            "tags": "not-a-list",  # Invalid format
        }

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is True
        assert result.tags == []

    async def test_rate_limit_error(self, processor_with_client):
        """Test handling rate limit error."""
        error = anthropic.RateLimitError(
            message="Rate limit exceeded", response=Mock(), body=None
        )

        processor_with_client.client.messages.create.side_effect = error

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "rate_limit"
        assert result.error_message == "API rate limit exceeded"

    async def test_timeout_error(self, processor_with_client):
        """Test handling timeout error."""
        processor_with_client.client.messages.create.side_effect = (
            anthropic.APITimeoutError("Request timed out")
        )

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "timeout"
        assert result.error_message == "API request timed out"

    async def test_api_status_error(self, processor_with_client):
        """Test handling API status error."""
        error = anthropic.APIStatusError(
            message="Bad request", response=Mock(), body=None
        )
        error.status_code = 400

        processor_with_client.client.messages.create.side_effect = error

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "api_error"
        assert "400" in result.error_message

    async def test_connection_error(self, processor_with_client):
        """Test handling connection error."""
        error = anthropic.APIConnectionError(request=Mock())

        processor_with_client.client.messages.create.side_effect = error

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "connection_error"
        assert result.error_message == "Failed to connect to Anthropic API"

    async def test_unexpected_error(self, processor_with_client):
        """Test handling unexpected error."""
        processor_with_client.client.messages.create.side_effect = RuntimeError(
            "Unexpected error"
        )

        result = await processor_with_client.process_content(
            "Test content", "text/plain"
        )

        assert result.success is False
        assert result.error_type == "unknown_error"
        assert "Unexpected error" in result.error_message

    async def test_different_content_types(self, processor_with_client):
        """Test processing different content types."""
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Title",
            "summary": "Test summary",
            "tags": ["test"],
        }

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        # Test HTML content
        result = await processor_with_client.process_content(
            "<html><body><h1>Test</h1><p>Content</p></body></html>", "text/html"
        )
        assert result.success is True

        # Test URL content
        result = await processor_with_client.process_content(
            "Article content from a web page", "url"
        )
        assert result.success is True

    async def test_content_truncation(self, processor_with_client):
        """Test that long content is properly truncated in the prompt."""
        # Create content longer than 3000 characters
        long_content = "A" * 4000

        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Long Content Title",
            "summary": "Summary of long content",
            "tags": ["long", "content"],
        }

        mock_response = Mock()
        mock_response.content = [mock_tool_use]

        processor_with_client.client.messages.create.return_value = mock_response

        result = await processor_with_client.process_content(long_content, "text/plain")

        assert result.success is True

        # Check that the API was called with truncated content
        call_args = processor_with_client.client.messages.create.call_args
        user_message = call_args[1]["messages"][0]["content"]

        # The message should contain the truncated content with "..."
        assert "..." in user_message
        assert len(user_message) < len(long_content) + 1000  # Account for prompt text

    def test_build_system_prompt(self, processor_with_client):
        """Test system prompt building."""
        prompt = processor_with_client._build_system_prompt()

        assert isinstance(prompt, str)
        assert "content analysis" in prompt.lower()
        assert "title" in prompt.lower()
        assert "summary" in prompt.lower()
        assert "tags" in prompt.lower()

    def test_build_user_message(self, processor_with_client):
        """Test user message building."""
        content = "Test content for analysis"
        content_type = "text/plain"

        message = processor_with_client._build_user_message(content, content_type)

        assert isinstance(message, str)
        assert content_type in message
        assert content in message
        assert "extract_content_data" in message

    def test_build_user_message_truncation(self, processor_with_client):
        """Test user message building with content truncation."""
        # Create content longer than 3000 characters
        long_content = "X" * 4000
        content_type = "text/plain"

        message = processor_with_client._build_user_message(long_content, content_type)

        assert "..." in message
        # The content in the message should be truncated
        content_in_message = message.split("Content:\n")[1].split("\n\nUse the")[0]
        assert len(content_in_message) <= 3003  # 3000 + "..."

    def test_llm_result_dataclass(self):
        """Test LLMResult dataclass functionality."""
        # Test successful result
        success_result = LLMResult(
            success=True,
            title="Test Title",
            summary="Test Summary",
            tags=["tag1", "tag2"],
        )

        assert success_result.success is True
        assert success_result.title == "Test Title"
        assert success_result.summary == "Test Summary"
        assert success_result.tags == ["tag1", "tag2"]
        assert success_result.error_message is None
        assert success_result.error_type is None

        # Test error result
        error_result = LLMResult(
            success=False, error_type="test_error", error_message="Test error message"
        )

        assert error_result.success is False
        assert error_result.error_type == "test_error"
        assert error_result.error_message == "Test error message"
        assert error_result.title is None
        assert error_result.summary is None
        assert error_result.tags is None
