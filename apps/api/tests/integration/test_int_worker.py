"""
Integration tests for worker task processing.

Tests:
- INT-024: Worker processes URL resource successfully
- INT-025: Worker processes text resource successfully
- INT-026: URL requires login, user has linked account — provider fetch succeeds
- INT-027: URL requires login, user has no linked account — FAILED
- INT-028: LLM processing fails — FAILED
"""

from unittest.mock import patch

import pytest
from httpx import Response

from models.account import Account
from models.resource import Resource, ResourceStatus
from models.user import User
from services.llm_processor import LLMResult
from services.tiered_url_fetcher import TieredFetchResult
from workers.tasks import process_resource


# Helper to create async context manager mock
async def mock_session_context(test_session):
    """Create an async context manager that yields the test session.

    Note: This pattern allows the worker and test to share the same database session,
    enabling transaction visibility between the worker execution and test verification.
    This is intentional for integration testing - the shared session ensures
    that changes made by the worker are immediately visible to test assertions
    without requiring separate database transactions.
    """

    class SessionContext:
        async def __aenter__(self):
            return test_session

        async def __aexit__(self, exc_type, exc, tb):
            pass

    return SessionContext()


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_processes_url_resource_successfully(db_session, respx_mock):
    """
    INT-024: Worker processes URL resource successfully
    """
    # Create user and resource
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="url",
        original_content="https://example.com/article",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock successful URL fetch (content must exceed 500-char bot-detection threshold)
    mock_html = (
        "<html><head><title>Test Article</title></head>"
        "<body>"
        "<h1>Test Article</h1>"
        "<p>This is a detailed article with enough content to pass the bot-detection "
        "threshold in the tiered URL fetcher. The fetcher requires at least 500 "
        "characters of meaningful content before it considers the page successfully "
        "fetched via HTTP. This paragraph provides that required content length so "
        "that the test does not inadvertently trigger the Playwright fallback path, "
        "which is not available in the CI environment.</p>"
        "</body></html>"
    )
    respx_mock.get("https://example.com/article").mock(
        return_value=Response(200, text=mock_html)
    )

    # Mock LLM processing with deterministic results
    mock_llm_result = LLMResult(
        success=True,
        title="Processed Article Title",
        summary="This is a processed summary of the article.",
        tags=["Technology", "Testing"],
        top_level_categories=["Science & Technology"],
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks.llm_processor_service.process_content",
        return_value=mock_llm_result,
    ):
        with patch("workers.tasks.graph_service.update_graph") as mock_graph:
            with patch(
                "workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx
            ):
                # Run the worker task
                result = await process_resource({}, str(resource.id))

    # Verify result
    assert result["status"] == "ready"
    assert result["resource_id"] == str(resource.id)
    assert "processed_at" in result
    assert result["title"] == "Processed Article Title"
    assert result["tags_count"] == 2
    assert "content_fetch" in result["stages_completed"]
    assert "llm_processing" in result["stages_completed"]
    assert "graph_update" in result["stages_completed"]

    # Verify resource in database
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.READY
    assert resource.title == "Processed Article Title"
    assert resource.summary == "This is a processed summary of the article."
    assert resource.tags == ["Technology", "Testing"]
    assert resource.status_message is None

    # Verify graph update was called
    mock_graph.assert_called_once_with(
        user.id, ["Technology", "Testing"], ["Science & Technology"]
    )


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_processes_text_resource_successfully(db_session):
    """
    INT-025: Worker processes text resource successfully
    """
    # Create user and resource
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="text",
        original_content="This is some text content to be processed by the LLM.",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock LLM processing with deterministic results
    mock_llm_result = LLMResult(
        success=True,
        title="Processed Text Title",
        summary="This is a processed summary of the text content.",
        tags=["Content", "Analysis"],
        top_level_categories=["Science & Technology"],
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks.llm_processor_service.process_content",
        return_value=mock_llm_result,
    ):
        with patch("workers.tasks.graph_service.update_graph") as mock_graph:
            with patch(
                "workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx
            ):
                # Run the worker task
                result = await process_resource({}, str(resource.id))

    # Verify result
    assert result["status"] == "ready"
    assert result["resource_id"] == str(resource.id)
    assert "processed_at" in result
    assert result["title"] == "Processed Text Title"
    assert result["tags_count"] == 2
    assert "content_direct" in result["stages_completed"]
    assert "llm_processing" in result["stages_completed"]
    assert "graph_update" in result["stages_completed"]

    # Verify resource in database
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.READY
    assert resource.title == "Processed Text Title"
    assert resource.summary == "This is a processed summary of the text content."
    assert resource.tags == ["Content", "Analysis"]
    assert resource.status_message is None

    # Verify graph update was called
    mock_graph.assert_called_once_with(
        user.id, ["Content", "Analysis"], ["Science & Technology"]
    )


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_url_requires_login_with_linked_account_succeeds(db_session):
    """
    INT-026: URL requires login, user has linked account — provider fetch succeeds

    Note: This is a service-layer test that mocks the url_fetcher_service to simulate
    successful provider-based authentication and content fetching. The service is
    assumed to handle 401 detection and provider retry internally.
    """
    # Create user with linked Twitter account
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        provider="twitter",
        provider_account_id="twitter-123",
        access_token="valid-token",
    )
    db_session.add(account)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="url",
        original_content="https://twitter.com/user/status/123",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock the tiered fetcher to return successful provider fetch
    # (simulates Tier 1 API fetch for a Twitter URL with linked account)
    mock_tweet_content = "This is tweet content fetched via Twitter API."
    mock_fetch_result = TieredFetchResult(
        success=True,
        content=mock_tweet_content,
        content_type="text/plain",
        fetch_tier="api",
    )

    # Mock LLM processing with deterministic results
    mock_llm_result = LLMResult(
        success=True,
        title="Twitter Post Analysis",
        summary="Analysis of the Twitter post content.",
        tags=["Social", "Twitter"],
        top_level_categories=["Science & Technology"],
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks._fetcher.fetch_url_content",
        return_value=mock_fetch_result,
    ):
        with patch(
            "workers.tasks.llm_processor_service.process_content",
            return_value=mock_llm_result,
        ):
            with patch("workers.tasks.graph_service.update_graph") as mock_graph:
                with patch(
                    "workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx
                ):
                    # Run the worker task
                    result = await process_resource({}, str(resource.id))

    # Verify result - should succeed with provider fetch
    assert result["status"] == "ready"
    assert result["resource_id"] == str(resource.id)
    assert result["title"] == "Twitter Post Analysis"
    assert result["tags_count"] == 2

    # Verify resource in database
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.READY
    assert resource.title == "Twitter Post Analysis"
    assert resource.summary == "Analysis of the Twitter post content."
    assert resource.tags == ["Social", "Twitter"]
    assert resource.status_message is None

    # Verify graph update was called
    mock_graph.assert_called_once_with(
        user.id, ["Social", "Twitter"], ["Science & Technology"]
    )


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_url_requires_login_no_linked_account_fails(db_session):
    """
    INT-027: URL requires login, user has no linked account — FAILED
    """
    # Create user WITHOUT linked account
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="url",
        original_content="https://twitter.com/user/status/456",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock the tiered fetcher to return AUTH_REQUIRED failure
    mock_fetch_result = TieredFetchResult(
        success=False,
        error_type="API_REQUIRED",
        error_message="Authentication required to fetch this URL.",
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks._fetcher.fetch_url_content",
        return_value=mock_fetch_result,
    ):
        with patch("workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx):
            # Run the worker task
            result = await process_resource({}, str(resource.id))

    # Verify result - should fail due to authentication required
    assert result["status"] == "failed"
    assert result["resource_id"] == str(resource.id)
    # API_REQUIRED maps to "...Go to Settings to link your account."
    assert "linked account" in result["error"]
    assert result["stage"] == "content_fetch"

    # Verify resource in database
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.FAILED
    assert "linked account" in resource.status_message
    assert resource.title is None
    assert resource.summary is None
    assert resource.tags is None or resource.tags == []


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_llm_processing_fails(db_session):
    """
    INT-028: LLM processing fails — FAILED
    """
    # Create user and resource
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="text",
        original_content="This text will cause LLM processing to fail.",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock LLM processing failure
    mock_llm_result = LLMResult(
        success=False,
        error_message="LLM service temporarily unavailable",
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks.llm_processor_service.process_content",
        return_value=mock_llm_result,
    ):
        with patch("workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx):
            # Run the worker task
            result = await process_resource({}, str(resource.id))

    # Verify result - should fail at LLM processing stage
    assert result["status"] == "failed"
    assert result["resource_id"] == str(resource.id)
    assert (
        result["error"] == "LLM processing failed: LLM service temporarily unavailable"
    )
    assert result["stage"] == "llm_processing"

    # Verify resource in database
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.FAILED
    assert (
        resource.status_message
        == "LLM processing failed: LLM service temporarily unavailable"
    )
    assert resource.title is None
    assert resource.summary is None
    assert resource.tags is None or resource.tags == []


@pytest.mark.integration
@pytest.mark.int_worker
async def test_worker_graph_update_fails_resource_still_ready(db_session):
    """
    Test that when graph_service.update_from_resource() raises an exception,
    the resource still ends up READY (graph failures should not cause job to FAIL).
    """
    # Create user and resource
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    resource = Resource(
        owner_id=user.id,
        content_type="text",
        original_content="This text will succeed but graph update will fail.",
        status=ResourceStatus.PENDING,
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.commit()

    # Mock LLM processing success
    mock_llm_result = LLMResult(
        success=True,
        title="Graph Test Article",
        summary="This is a test article for graph failure handling.",
        tags=["Test", "Graph"],  # Ensure enough tags to trigger graph update
        top_level_categories=["Science & Technology"],
    )

    # Mock AsyncSessionLocal to return test session
    mock_session_ctx = await mock_session_context(db_session)

    with patch(
        "workers.tasks.llm_processor_service.process_content",
        return_value=mock_llm_result,
    ):
        with patch(
            "workers.tasks.graph_service.update_graph",
            side_effect=Exception("Graph service unavailable"),
        ) as mock_graph:
            with patch(
                "workers.tasks.AsyncSessionLocal", return_value=mock_session_ctx
            ):
                # Run the worker task
                result = await process_resource({}, str(resource.id))

    # Verify result - should still be ready despite graph failure
    assert result["status"] == "ready"
    assert result["resource_id"] == str(resource.id)
    assert result["title"] == "Graph Test Article"
    assert result["tags_count"] == 2
    assert "graph_update" in result["stages_completed"]

    # Verify resource in database - should be READY
    await db_session.refresh(resource)
    assert resource.status == ResourceStatus.READY
    assert resource.title == "Graph Test Article"
    assert resource.summary == "This is a test article for graph failure handling."
    assert resource.tags == ["Test", "Graph"]
    assert resource.status_message is None

    # Verify graph update was attempted
    mock_graph.assert_called_once_with(
        user.id, ["Test", "Graph"], ["Science & Technology"]
    )
