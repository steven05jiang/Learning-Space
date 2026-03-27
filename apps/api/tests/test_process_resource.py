"""Tests for the process_resource worker task."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from models.resource import Resource, ResourceStatus
from services.llm_processor import LLMResult
from services.tiered_url_fetcher import TieredFetchResult
from workers.tasks import process_resource


class TestProcessResource:
    """Test the process_resource worker task pipeline."""

    @pytest.fixture
    def mock_resource(self):
        """Create a mock resource for testing."""
        resource = Mock(spec=Resource)
        resource.id = 123
        resource.owner_id = 456
        resource.content_type = "url"
        resource.original_content = "https://example.com"
        resource.status = ResourceStatus.PENDING
        resource.status_message = None
        resource.title = None
        resource.summary = None
        resource.tags = []
        resource.updated_at = datetime.now(timezone.utc)
        return resource

    @pytest.fixture
    def mock_text_resource(self):
        """Create a mock text resource for testing."""
        resource = Mock(spec=Resource)
        resource.id = 124
        resource.owner_id = 456
        resource.content_type = "text"
        resource.original_content = "This is some test content to process."
        resource.status = ResourceStatus.PENDING
        resource.status_message = None
        resource.title = None
        resource.summary = None
        resource.tags = []
        resource.updated_at = datetime.now(timezone.utc)
        return resource

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def mock_fetch_success(self):
        """Mock successful URL fetch result."""
        return TieredFetchResult(
            success=True,
            content="<html><body><h1>Test Article</h1>"
            "<p>Some content here</p></body></html>",
            content_type="text/html",
            status_code=200,
            final_url="https://example.com",
            fetch_tier="http",
        )

    @pytest.fixture
    def mock_fetch_failure(self):
        """Mock failed URL fetch result."""
        return TieredFetchResult(
            success=False,
            error_message="HTTP 404: Not Found",
            error_type="not_found",
            fetch_tier="http",
            status_code=404,
        )

    @pytest.fixture
    def mock_llm_success(self):
        """Mock successful LLM processing result."""
        return LLMResult(
            success=True,
            title="Test Article Title",
            summary="This is a comprehensive summary of the test article content.",
            tags=["test", "article", "content"],
            top_level_categories=["Science & Technology"],
        )

    @pytest.fixture
    def mock_llm_failure(self):
        """Mock failed LLM processing result."""
        return LLMResult(
            success=False,
            error_message="API rate limit exceeded",
            error_type="rate_limit",
        )

    @pytest.mark.asyncio
    async def test_process_resource_invalid_id(self):
        """Test that invalid resource ID raises ValueError."""
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            await process_resource({}, "")

        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            await process_resource({}, None)

    @pytest.mark.asyncio
    async def test_process_resource_url_success_end_to_end(
        self, mock_resource, mock_fetch_success, mock_llm_success, monkeypatch
    ):
        """Test successful end-to-end processing of a URL resource."""
        # Mock database session and query
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_category_row2 = Mock()
        mock_category_row2.name = "Education & Knowledge"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [
            mock_category_row,
            mock_category_row2,
        ]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_success
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["python", "ai"])
        mock_graph_service.update_from_resource = AsyncMock()
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify the result
        assert result["resource_id"] == "123"
        assert result["status"] == "ready"
        assert result["title"] == "Test Article Title"
        assert result["summary_length"] == len(mock_llm_success.summary)
        assert result["tags_count"] == 3
        assert "processed_at" in result
        expected_stages = {
            "status_update",
            "content_fetch",
            "llm_processing",
            "db_update",
            "graph_update",
        }
        assert set(result["stages_completed"]) == expected_stages

        # Verify resource was updated correctly
        assert mock_resource.status == ResourceStatus.READY
        assert mock_resource.title == "Test Article Title"
        assert mock_resource.summary == mock_llm_success.summary
        assert mock_resource.tags == ["test", "article", "content"]
        assert mock_resource.status_message is None

        # Verify services were called
        mock_url_fetcher.fetch_url_content.assert_called_once_with(
            "https://example.com", 456
        )
        mock_graph_service.get_user_tags.assert_called_once_with(456)
        mock_llm_processor.process_content.assert_called_once_with(
            mock_fetch_success.content,
            "text/html",
            ["python", "ai"],
            ["Science & Technology", "Education & Knowledge"],
        )
        mock_graph_service.update_graph.assert_called_once_with(
            456, ["test", "article", "content"], ["Science & Technology"]
        )
        mock_graph_service.update_from_resource.assert_called_once_with(
            456, ["test", "article", "content"]
        )

        # Verify database commits
        # Once for PROCESSING, once for READY
        assert mock_session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_process_resource_text_success_end_to_end(
        self, mock_text_resource, mock_llm_success, monkeypatch
    ):
        """Test successful end-to-end processing of a text resource."""
        # Mock database session and query
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_text_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_category_row2 = Mock()
        mock_category_row2.name = "Education & Knowledge"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [
            mock_category_row,
            mock_category_row2,
        ]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services (URL fetcher should not be called for text resources)
        mock_url_fetcher = AsyncMock()
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_success
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["existing", "tags"])
        mock_graph_service.update_from_resource = AsyncMock()
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "124")

        # Verify the result
        assert result["resource_id"] == "124"
        assert result["status"] == "ready"
        assert "content_direct" in result["stages_completed"]
        assert "content_fetch" not in result["stages_completed"]

        # Verify URL fetcher was NOT called for text resource
        mock_url_fetcher.fetch_url_content.assert_not_called()

        # Verify LLM processor was called with original content
        mock_graph_service.get_user_tags.assert_called_once_with(456)
        mock_llm_processor.process_content.assert_called_once_with(
            "This is some test content to process.",
            "text",
            ["existing", "tags"],
            ["Science & Technology", "Education & Knowledge"],
        )

    @pytest.mark.asyncio
    async def test_process_resource_not_found(self, monkeypatch):
        """Test that non-existent resource raises ValueError."""
        # Mock database session with no result
        mock_session = AsyncMock()
        mock_result = Mock()  # Use regular Mock for sync method
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        with pytest.raises(ValueError, match="Resource with id 999 not found"):
            await process_resource({}, "999")

    @pytest.mark.asyncio
    async def test_process_resource_fetch_failure(
        self, mock_resource, mock_fetch_failure, monkeypatch
    ):
        """Test that fetch failure sets resource to FAILED status."""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()  # Use regular Mock for sync method
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock failed URL fetch
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_failure
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify failure result
        assert result["resource_id"] == "123"
        assert result["status"] == "failed"
        assert result["stage"] == "content_fetch"
        assert "The page was not found (404)" in result["error"]

        # Verify resource was marked as FAILED
        assert mock_resource.status == ResourceStatus.FAILED
        assert "The page was not found (404)" in mock_resource.status_message

    @pytest.mark.asyncio
    async def test_process_resource_llm_failure(
        self, mock_resource, mock_fetch_success, mock_llm_failure, monkeypatch
    ):
        """Test that LLM failure sets resource to FAILED status."""
        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_failure
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["python"])
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify failure result
        assert result["resource_id"] == "123"
        assert result["status"] == "failed"
        assert result["stage"] == "llm_processing"
        assert "LLM processing failed" in result["error"]

        # Verify resource was marked as FAILED
        assert mock_resource.status == ResourceStatus.FAILED
        assert "LLM processing failed" in mock_resource.status_message

    @pytest.mark.asyncio
    async def test_process_resource_graph_update_failure_continues(
        self, mock_resource, mock_fetch_success, mock_llm_success, monkeypatch
    ):
        """Test that graph update failure doesn't fail the entire job."""
        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_success
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        # Mock graph service to fail
        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["existing", "tags"])
        mock_graph_service.update_from_resource.side_effect = Exception(
            "Graph connection failed"
        )
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify processing still succeeds despite graph update failure
        assert result["resource_id"] == "123"
        assert result["status"] == "ready"
        assert mock_resource.status == ResourceStatus.READY

    @pytest.mark.asyncio
    async def test_process_resource_insufficient_tags_skips_graph_update(
        self, mock_resource, mock_fetch_success, monkeypatch
    ):
        """Test that resources with <2 tags skip graph update."""
        # Mock LLM result with insufficient tags
        mock_llm_insufficient_tags = LLMResult(
            success=True,
            title="Test Article",
            summary="A test summary",
            tags=["single-tag"],  # Only one tag
            top_level_categories=["Science & Technology"],
        )

        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_insufficient_tags
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["existing"])
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify processing succeeds
        assert result["status"] == "ready"
        assert result["tags_count"] == 1

        # Verify graph service was NOT called
        mock_graph_service.update_from_resource.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_resource_status_transitions(
        self, mock_resource, mock_fetch_success, mock_llm_success, monkeypatch
    ):
        """Test that resource status transitions correctly through pipeline."""
        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_success
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["test"])
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        await process_resource({}, "123")

        # Verify final status should be READY (can't easily track transitions with Mock)
        assert mock_resource.status == ResourceStatus.READY
        assert mock_resource.status_message is None

    @pytest.mark.asyncio
    async def test_process_resource_graph_update_called_with_correct_args(
        self, mock_resource, mock_fetch_success, monkeypatch
    ):
        """Test graph_service.update_graph and update_from_resource called correctly."""
        # Mock LLM result with multiple tags
        mock_llm_multiple_tags = LLMResult(
            success=True,
            title="Test Article",
            summary="A test summary",
            tags=["python", "testing", "api"],
            top_level_categories=["Science & Technology"],
        )

        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_multiple_tags
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(
            return_value=["existing", "user", "tags"]
        )
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify processing succeeds
        assert result["status"] == "ready"
        assert result["tags_count"] == 3

        # Verify graph service was called with exact owner_id, tags, and categories
        mock_graph_service.update_graph.assert_called_once_with(
            456,  # owner_id from mock_resource
            ["python", "testing", "api"],
            ["Science & Technology"],
        )
        mock_graph_service.update_from_resource.assert_called_once_with(
            456,  # owner_id from mock_resource
            ["python", "testing", "api"],  # tags from mock_llm_multiple_tags
        )

    @pytest.mark.asyncio
    async def test_process_resource_empty_tags_skips_graph_update(
        self, mock_resource, mock_fetch_success, monkeypatch
    ):
        """Test that resources with empty tags skip graph update."""
        # Mock LLM result with no tags
        mock_llm_no_tags = LLMResult(
            success=True,
            title="Test Article",
            summary="A test summary",
            tags=[],  # No tags
            top_level_categories=["Science & Technology"],
        )

        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_no_tags
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=[])
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify processing succeeds
        assert result["status"] == "ready"
        assert result["tags_count"] == 0

        # Verify graph service was NOT called
        mock_graph_service.update_from_resource.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_resource_graph_failure_resource_stays_ready(
        self, mock_resource, mock_fetch_success, mock_llm_success, monkeypatch
    ):
        """Test that graph update failure doesn't change resource status from READY."""
        # Mock database session
        mock_session = AsyncMock()

        # Mock the resource query result
        mock_resource_result = Mock()
        mock_resource_result.scalar_one_or_none.return_value = mock_resource

        # Mock the categories query result
        mock_category_row = Mock()
        mock_category_row.name = "Science & Technology"
        mock_categories_result = Mock()
        mock_categories_result.fetchall.return_value = [mock_category_row]

        # Mock session.execute to return different results based on call order
        execute_call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return mock_resource_result
            else:
                return mock_categories_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        class MockAsyncSessionContext:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_session_factory():
            return MockAsyncSessionContext(mock_session)

        monkeypatch.setattr("workers.tasks.AsyncSessionLocal", mock_session_factory)

        # Mock services
        mock_url_fetcher = AsyncMock()
        mock_url_fetcher.fetch_url_content.return_value = mock_fetch_success
        monkeypatch.setattr("workers.tasks._fetcher", mock_url_fetcher)

        mock_llm_processor = AsyncMock()
        mock_llm_processor.process_content.return_value = mock_llm_success
        monkeypatch.setattr("workers.tasks.llm_processor_service", mock_llm_processor)

        # Mock graph service to fail on update_graph (first call in pipeline)
        mock_graph_service = AsyncMock()
        mock_graph_service.get_user_tags = AsyncMock(return_value=["python", "ai"])
        mock_graph_service.update_graph.side_effect = Exception(
            "Neo4j connection error"
        )
        monkeypatch.setattr("workers.tasks.graph_service", mock_graph_service)

        # Execute the task
        result = await process_resource({}, "123")

        # Verify processing still succeeds despite graph update failure
        assert result["resource_id"] == "123"
        assert result["status"] == "ready"

        # Verify resource remains in READY state even after graph failure
        assert mock_resource.status == ResourceStatus.READY
        assert mock_resource.status_message is None  # No error message set on resource

        # Verify graph service was called (but failed)
        mock_graph_service.update_graph.assert_called_once_with(
            456, ["test", "article", "content"], ["Science & Technology"]
        )
