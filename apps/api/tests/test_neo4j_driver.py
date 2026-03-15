"""
Tests for Neo4j driver service.
"""

import contextlib
from unittest.mock import AsyncMock, patch

import pytest

from services.neo4j_driver import Neo4jDriverService


@pytest.fixture
def neo4j_service():
    """Create a fresh Neo4j service instance for testing."""
    return Neo4jDriverService()


@pytest.mark.asyncio
async def test_connect_and_create_constraints(neo4j_service):
    """Test that connect() establishes connection and creates constraints."""
    # Mock the driver and session
    mock_driver = AsyncMock()
    mock_session = AsyncMock()

    # Mock the driver.session() to return an async context manager
    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.session = lambda: mock_session_context()

    with patch(
        "services.neo4j_driver.AsyncGraphDatabase.driver", return_value=mock_driver
    ):
        # Mock successful connectivity verification
        mock_driver.verify_connectivity = AsyncMock()

        await neo4j_service.connect()

        # Verify connectivity was checked
        mock_driver.verify_connectivity.assert_called_once()

        # Verify constraint creation was attempted
        expected_constraint = (
            "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR "
            "(t:Tag) REQUIRE t.name IS UNIQUE"
        )
        mock_session.run.assert_called_with(expected_constraint)


@pytest.mark.asyncio
async def test_connect_failure_cleanup(neo4j_service):
    """Test that connection failure properly cleans up."""
    mock_driver = AsyncMock()
    mock_driver.verify_connectivity.side_effect = Exception("Connection failed")
    mock_driver.close = AsyncMock()

    with patch(
        "services.neo4j_driver.AsyncGraphDatabase.driver", return_value=mock_driver
    ):
        with pytest.raises(Exception, match="Connection failed"):
            await neo4j_service.connect()

        # Verify cleanup was called
        mock_driver.close.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_healthy(neo4j_service):
    """Test health check with healthy connection."""
    # Setup mock driver and session
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_record = {"test": 1}

    mock_session.run.return_value = mock_result
    mock_result.single.return_value = mock_record

    # Mock the driver.session() to return an async context manager
    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.session = lambda: mock_session_context()

    neo4j_service._driver = mock_driver

    result = await neo4j_service.health_check()

    assert result["status"] == "healthy"
    assert "successful" in result["message"]


@pytest.mark.asyncio
async def test_health_check_no_driver(neo4j_service):
    """Test health check when driver is not connected."""
    # Driver is None by default
    result = await neo4j_service.health_check()

    assert result["status"] == "error"
    assert "not connected" in result["message"]


@pytest.mark.asyncio
async def test_health_check_exception(neo4j_service):
    """Test health check when Neo4j query fails."""
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_session.run.side_effect = Exception("Query failed")

    # Mock the driver.session() to return an async context manager
    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.session = lambda: mock_session_context()

    neo4j_service._driver = mock_driver

    result = await neo4j_service.health_check()

    assert result["status"] == "error"
    assert "Query failed" in result["message"]


@pytest.mark.asyncio
async def test_disconnect(neo4j_service):
    """Test disconnection from Neo4j."""
    mock_driver = AsyncMock()
    neo4j_service._driver = mock_driver

    await neo4j_service.disconnect()

    mock_driver.close.assert_called_once()
    assert neo4j_service._driver is None


def test_get_session_no_driver(neo4j_service):
    """Test that get_session raises error when driver not connected."""
    with pytest.raises(RuntimeError, match="Neo4j driver not connected"):
        neo4j_service.get_session()
