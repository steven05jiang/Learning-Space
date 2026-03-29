"""Tests for resource search endpoint (GET /resources/search)."""

from datetime import datetime
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.resource_search_service import ResourceSearchItem, SearchResult


class TestResourceSearch:
    """Test cases for GET /resources/search."""

    @pytest.mark.asyncio
    async def test_search_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user: User,
    ):
        """Test successful resource search."""
        # Mock the search service to return controlled results
        mock_search_item = ResourceSearchItem(
            id="test-resource-id",
            title="Test Resource",
            summary="A test resource for search",
            tags=["test", "search"],
            top_level_categories=["Technology"],
            original_content="https://example.com/test",
            content_type="url",
            status="READY",
            created_at=datetime.fromisoformat("2026-03-28T00:00:00"),
            updated_at=datetime.fromisoformat("2026-03-28T00:00:00"),
            rank=0.85,
        )
        mock_result = SearchResult(resources=[mock_search_item], total=1)

        with patch(
            "services.resource_search_service.ResourceSearchService.search"
        ) as mock_search:
            mock_search.return_value = mock_result

            response = await client.get(
                "/resources/search",
                params={"q": "test query"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "resources" in data
            assert "total" in data
            assert data["total"] == 1
            assert len(data["resources"]) == 1

            resource = data["resources"][0]
            assert resource["id"] == "test-resource-id"
            assert resource["title"] == "Test Resource"
            assert resource["rank"] == 0.85
            assert resource["status"] == "READY"
            assert resource["tags"] == ["test", "search"]

            # Verify the search service was called with correct parameters
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["owner_id"] == test_user.id
            assert call_args[1]["query"] == "test query"
            assert call_args[1]["tag"] is None
            assert call_args[1]["limit"] == 20
            assert call_args[1]["offset"] == 0

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test search with tag filter and pagination parameters."""
        mock_result = SearchResult(resources=[], total=0)

        with patch(
            "services.resource_search_service.ResourceSearchService.search"
        ) as mock_search:
            mock_search.return_value = mock_result

            response = await client.get(
                "/resources/search",
                params={
                    "q": "machine learning",
                    "tag": "AI",
                    "limit": 10,
                    "offset": 5,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["resources"] == []

            # Verify the search service was called with correct parameters
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["query"] == "machine learning"
            assert call_args[1]["tag"] == "AI"
            assert call_args[1]["limit"] == 10
            assert call_args[1]["offset"] == 5

    @pytest.mark.asyncio
    async def test_search_empty_query_error(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test error response for empty search query."""
        response = await client.get(
            "/resources/search",
            params={"q": "   "},  # Whitespace only
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "SEARCH_QUERY_EMPTY"
        assert data["detail"]["message"] == "Search query cannot be empty"

    @pytest.mark.asyncio
    async def test_search_query_too_long_error(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test error response for query exceeding 500 characters."""
        long_query = "a" * 501  # 501 characters

        response = await client.get(
            "/resources/search",
            params={"q": long_query},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "SEARCH_QUERY_TOO_LONG"
        assert data["detail"]["message"] == "Search query exceeds 500 characters"

    @pytest.mark.asyncio
    async def test_search_unauthenticated(self, client: AsyncClient):
        """Test error response for unauthenticated request."""
        response = await client.get(
            "/resources/search",
            params={"q": "test query"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_search_invalid_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test validation error for invalid limit parameter."""
        response = await client.get(
            "/resources/search",
            params={"q": "test", "limit": 0},  # Invalid: must be >= 1
            headers=auth_headers,
        )

        assert response.status_code == 422

        response = await client.get(
            "/resources/search",
            params={"q": "test", "limit": 101},  # Invalid: must be <= 100
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_invalid_offset(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test validation error for invalid offset parameter."""
        response = await client.get(
            "/resources/search",
            params={"q": "test", "offset": -1},  # Invalid: must be >= 0
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_minimal_query(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test search with minimal valid query (1 character)."""
        mock_result = SearchResult(resources=[], total=0)

        with patch(
            "services.resource_search_service.ResourceSearchService.search"
        ) as mock_search:
            mock_search.return_value = mock_result

            response = await client.get(
                "/resources/search",
                params={"q": "a"},  # Minimal valid query
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["query"] == "a"

    @pytest.mark.asyncio
    async def test_search_maximum_query(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test search with maximum valid query (500 characters)."""
        mock_result = SearchResult(resources=[], total=0)
        max_query = "a" * 500  # Exactly 500 characters

        with patch(
            "services.resource_search_service.ResourceSearchService.search"
        ) as mock_search:
            mock_search.return_value = mock_result

            response = await client.get(
                "/resources/search",
                params={"q": max_query},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["query"] == max_query
