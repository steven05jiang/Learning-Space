"""Tests for LLM processor category validation and context features (DEV-062)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.llm_processor import LLMProcessorService, LLMResult


class TestLLMProcessorCategories:
    """Test the new category validation and context features."""

    @pytest.fixture
    def llm_service(self):
        """Create LLM processor service for testing."""
        service = LLMProcessorService(api_key="test-key")
        # Mock the client to avoid actual API calls
        service.client = Mock()
        return service

    @pytest.fixture
    def mock_existing_tags(self):
        """Mock existing user tags."""
        return ["machine-learning", "python", "data-science"]

    @pytest.fixture
    def mock_valid_categories(self):
        """Mock valid categories."""
        return [
            "Science & Technology",
            "Business & Economics",
            "Education & Knowledge",
            "Health & Medicine"
        ]

    def test_build_system_prompt_with_context(self, llm_service, mock_existing_tags, mock_valid_categories):
        """Test that system prompt includes existing tags and valid categories."""
        prompt = llm_service._build_system_prompt(mock_existing_tags, mock_valid_categories)

        # Check that existing tags are included
        assert "machine-learning" in prompt
        assert "python" in prompt
        assert "data-science" in prompt
        assert "reuse when applicable" in prompt

        # Check that valid categories are included
        assert "Science & Technology" in prompt
        assert "Business & Economics" in prompt
        assert "Education & Knowledge" in prompt
        assert "Health & Medicine" in prompt
        assert "Available categories" in prompt

    def test_build_system_prompt_without_context(self, llm_service):
        """Test system prompt with default categories when no context provided."""
        prompt = llm_service._build_system_prompt()

        # Should include default categories
        assert "Science & Technology" in prompt
        assert "Politics & Government" in prompt
        assert "Lifestyle & Personal Life" in prompt
        assert "Categories from:" in prompt

    @pytest.mark.asyncio
    async def test_process_content_valid_categories(self, llm_service, mock_valid_categories):
        """Test successful processing with valid categories."""
        # Mock successful Anthropic API response
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Machine Learning Basics",
            "summary": "An introduction to machine learning concepts and applications.",
            "tags": ["machine-learning", "ai", "python"],
            "top_level_categories": ["Science & Technology", "Education & Knowledge"]
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Content about machine learning",
            "text/plain",
            existing_user_tags=["machine-learning"],
            valid_categories=mock_valid_categories
        )

        assert result.success is True
        assert result.title == "Machine Learning Basics"
        assert "machine-learning" in result.tags
        assert "Science & Technology" in result.top_level_categories
        assert "Education & Knowledge" in result.top_level_categories
        assert result.error_type is None

    @pytest.mark.asyncio
    async def test_process_content_invalid_category(self, llm_service, mock_valid_categories):
        """Test processing fails with invalid category."""
        # Mock Anthropic API response with invalid category
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": ["Invalid Category", "Science & Technology"]
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain",
            valid_categories=mock_valid_categories
        )

        assert result.success is False
        assert result.error_type == "INVALID_CATEGORY"
        assert "Invalid Category" in result.error_message
        assert "not a valid category" in result.error_message

    @pytest.mark.asyncio
    async def test_process_content_empty_categories(self, llm_service, mock_valid_categories):
        """Test processing fails when no categories provided."""
        # Mock Anthropic API response with empty categories
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": []
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain",
            valid_categories=mock_valid_categories
        )

        assert result.success is False
        assert result.error_type == "CATEGORY_REQUIRED"
        assert "At least one top-level category is required" in result.error_message

    @pytest.mark.asyncio
    async def test_process_content_missing_categories_field(self, llm_service, mock_valid_categories):
        """Test processing fails when categories field is not a list."""
        # Mock Anthropic API response with non-list categories
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": "Science & Technology"  # String instead of list
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain",
            valid_categories=mock_valid_categories
        )

        assert result.success is False
        assert result.error_type == "CATEGORY_REQUIRED"
        assert "At least one top-level category is required" in result.error_message

    @pytest.mark.asyncio
    async def test_process_content_partial_valid_categories(self, llm_service, mock_valid_categories):
        """Test processing with mix of valid and invalid categories."""
        # Mock Anthropic API response with mix of valid/invalid categories
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": ["Science & Technology", "Invalid Category", "Education & Knowledge"]
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain",
            valid_categories=mock_valid_categories
        )

        # Should fail on first invalid category encountered
        assert result.success is False
        assert result.error_type == "INVALID_CATEGORY"
        assert "Invalid Category" in result.error_message

    @pytest.mark.asyncio
    async def test_process_content_default_categories_when_none_provided(self, llm_service):
        """Test processing uses default categories when none provided."""
        # Mock Anthropic API response with default category
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": ["Science & Technology"]
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain"
            # No existing_user_tags or valid_categories provided
        )

        assert result.success is True
        assert "Science & Technology" in result.top_level_categories

    @pytest.mark.asyncio
    async def test_process_content_limits_categories_to_three(self, llm_service, mock_valid_categories):
        """Test that categories are limited to maximum of 3."""
        # Mock Anthropic API response with more than 3 categories
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.input = {
            "title": "Test Article",
            "summary": "Test summary",
            "tags": ["test"],
            "top_level_categories": [
                "Science & Technology",
                "Business & Economics",
                "Education & Knowledge",
                "Health & Medicine"  # This should be trimmed
            ]
        }
        mock_response.content = [mock_tool_use]
        llm_service.client.messages.create = Mock(return_value=mock_response)

        result = await llm_service.process_content(
            "Test content",
            "text/plain",
            valid_categories=mock_valid_categories
        )

        assert result.success is True
        assert len(result.top_level_categories) == 3
        assert "Science & Technology" in result.top_level_categories
        assert "Business & Economics" in result.top_level_categories
        assert "Education & Knowledge" in result.top_level_categories
        # Fourth category should be trimmed
        assert "Health & Medicine" not in result.top_level_categories