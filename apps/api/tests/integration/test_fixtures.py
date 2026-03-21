"""Test file to verify integration test fixtures work correctly."""

import pytest

from tests.integration.factories import make_resource, make_resource_data


@pytest.mark.integration
async def test_db_session_fixture(db_session):
    """Test that the db_session fixture works correctly."""
    assert db_session is not None
    # Session should be ready for use
    await db_session.execute("SELECT 1")


@pytest.mark.integration
async def test_test_user_fixture(test_user):
    """Test that the test_user fixture creates a user correctly."""
    assert test_user.id is not None
    assert test_user.email == "integrationtest@example.com"
    assert test_user.display_name == "Integration Test User"


@pytest.mark.integration
async def test_auth_headers_fixture(auth_headers, test_user):
    """Test that the auth_headers fixture provides valid headers."""
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.integration
async def test_mock_llm_fixture(mock_llm):
    """Test that the mock_llm fixture provides a working LLM service."""
    result = await mock_llm.process_content("test content", "text/plain")
    assert result.success is True
    assert result.title is not None
    assert result.summary is not None
    assert result.tags is not None


@pytest.mark.integration
async def test_mock_fetch_fixture(mock_fetch):
    """Test that the mock_fetch fixture provides working HTTP responses."""
    response = await mock_fetch["mock_fetch"]("https://example.com/article")
    assert response["status_code"] == 200
    assert response["success"] is True
    assert "Test Article" in response["content"]


@pytest.mark.integration
async def test_mock_oauth_fixture(mock_oauth):
    """Test that the mock_oauth fixture provides OAuth data."""
    assert "google" in mock_oauth
    assert "user_info" in mock_oauth["google"]
    assert mock_oauth["google"]["user_info"]["email"] == "test@example.com"


@pytest.mark.integration
async def test_make_resource_factory(db_session, test_user):
    """Test that the make_resource factory works correctly."""
    resource = await make_resource(
        db_session,
        test_user,
        content_type="url",
        original_content="https://test.example.com"
    )

    assert resource.id is not None
    assert resource.owner_id == test_user.id
    assert resource.content_type == "url"
    assert resource.original_content == "https://test.example.com"
    assert resource.title is not None
    assert resource.summary is not None
    assert resource.tags is not None


@pytest.mark.integration
def test_make_resource_data_factory():
    """Test that the make_resource_data factory works correctly."""
    data = make_resource_data(
        content_type="url",
        original_content="https://example.com/test"
    )

    assert data["content_type"] == "url"
    assert data["original_content"] == "https://example.com/test"