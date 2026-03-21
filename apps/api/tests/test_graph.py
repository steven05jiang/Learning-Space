"""Tests for graph endpoints."""

import contextlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus
from models.user import User


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create a second test user in the database."""
    user = User(
        email="other@example.com",
        display_name="Other User",
        avatar_url="https://example.com/avatar2.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetNodeResources:
    """Test cases for GET /graph/nodes/{node_id}/resources."""

    async def test_get_node_resources_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test successful retrieval of resources for a node."""
        # Create test resources with tags
        resource1 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/1",
            title="Resource 1",
            summary="Summary 1",
            tags=["python", "web"],
            status=ResourceStatus.READY,
        )
        resource2 = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Text content 2",
            title="Resource 2",
            summary="Summary 2",
            tags=["python", "machine-learning"],
            status=ResourceStatus.READY,
        )
        resource3 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/3",
            title="Resource 3",
            summary="Summary 3",
            tags=["javascript", "web"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([resource1, resource2, resource3])
        await db_session.commit()

        # Get resources for "python" tag
        response = await client.get(
            "/graph/nodes/python/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 2 resources with "python" tag
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["limit"] == 50  # Default limit parameter
        assert data["offset"] == 0

        # Check that both resources are returned
        resource_ids = [item["id"] for item in data["items"]]
        assert str(resource1.id) in resource_ids
        assert str(resource2.id) in resource_ids
        assert str(resource3.id) not in resource_ids

        # Verify resource structure includes required fields
        for item in data["items"]:
            assert "id" in item
            assert "title" in item
            assert "summary" in item
            assert "original_content" in item
            assert "content_type" in item
            assert "status" in item
            assert "created_at" in item
            assert "tags" in item
            assert "python" in item["tags"]

    async def test_get_node_resources_empty_result(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test retrieval when no resources match the tag."""
        # Create a resource without the searched tag
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="Resource",
            summary="Summary",
            tags=["different-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/nonexistent-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0
        assert data["limit"] == 50  # Default limit parameter
        assert data["offset"] == 0

    async def test_get_node_resources_owner_scoped(
        self,
        client: AsyncClient,
        test_user: User,
        other_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that resources are scoped to the authenticated user."""
        # Create resources for both users with same tag
        user_resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/user",
            title="User Resource",
            tags=["shared-tag"],
            status=ResourceStatus.READY,
        )
        other_resource = Resource(
            owner_id=other_user.id,
            content_type="url",
            original_content="https://example.com/other",
            title="Other Resource",
            tags=["shared-tag"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([user_resource, other_resource])
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/shared-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only return the authenticated user's resource
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(user_resource.id)
        assert data["items"][0]["title"] == "User Resource"

    async def test_get_node_resources_url_field(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that url field is populated correctly for URL content type."""
        # Create URL and text resources
        url_resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="URL Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        text_resource = Resource(
            owner_id=test_user.id,
            content_type="text",
            original_content="Some text content",
            title="Text Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )

        db_session.add_all([url_resource, text_resource])
        await db_session.commit()

        response = await client.get(
            "/graph/nodes/test-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 2

        # Find the URL resource in response
        url_item = next(
            item for item in data["items"] if item["id"] == str(url_resource.id)
        )
        text_item = next(
            item for item in data["items"] if item["id"] == str(text_resource.id)
        )

        # URL resource should have original_content with URL and content_type "url"
        assert url_item["original_content"] == "https://example.com"
        assert url_item["content_type"] == "url"

        # Text resource should have original_content with text and content_type "text"
        assert text_item["original_content"] == "Some text content"
        assert text_item["content_type"] == "text"

    async def test_get_node_resources_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/graph/nodes/test-tag/resources")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_node_resources_partial_tag_match(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that partial tag matches are not returned (exact match required)."""
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com",
            title="Resource",
            tags=["python-advanced"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource)
        await db_session.commit()

        # Search for "python" should not match "python-advanced"
        response = await client.get(
            "/graph/nodes/python/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_get_node_resources_ordering(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that resources are ordered by created_at descending."""
        # Create resources with explicit ordering (newer first)
        resource1 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/1",
            title="Older Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource1)
        await db_session.commit()
        await db_session.refresh(resource1)

        resource2 = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content="https://example.com/2",
            title="Newer Resource",
            tags=["test-tag"],
            status=ResourceStatus.READY,
        )
        db_session.add(resource2)
        await db_session.commit()
        await db_session.refresh(resource2)

        response = await client.get(
            "/graph/nodes/test-tag/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 2
        # Newer resource should be first
        assert data["items"][0]["id"] == str(resource2.id)
        assert data["items"][0]["title"] == "Newer Resource"
        assert data["items"][1]["id"] == str(resource1.id)
        assert data["items"][1]["title"] == "Older Resource"

    async def test_get_node_resources_custom_limit(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test custom limit parameter returns at most specified number of items."""
        # Create 3 resources with the same tag
        resources = []
        for i in range(3):
            resource = Resource(
                owner_id=test_user.id,
                content_type="url",
                original_content=f"https://example.com/{i}",
                title=f"Resource {i}",
                tags=["test-tag"],
                status=ResourceStatus.READY,
            )
            resources.append(resource)

        db_session.add_all(resources)
        await db_session.commit()

        # Request with limit=1, should return only 1 item even though 3 match
        response = await client.get(
            "/graph/nodes/test-tag/resources?limit=1",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 3  # Total matching resources
        assert len(data["items"]) == 1  # But only 1 returned due to limit
        assert data["limit"] == 1
        assert data["offset"] == 0

    async def test_get_node_resources_pagination_offset(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test offset parameter skips the specified number of items."""
        # Create 3 resources with the same tag
        resources = []
        for i in range(3):
            resource = Resource(
                owner_id=test_user.id,
                content_type="url",
                original_content=f"https://example.com/{i}",
                title=f"Resource {i}",
                tags=["test-tag"],
                status=ResourceStatus.READY,
            )
            resources.append(resource)

        db_session.add_all(resources)
        await db_session.commit()

        # Get all resources first to know the order
        response_all = await client.get(
            "/graph/nodes/test-tag/resources",
            headers=auth_headers,
        )
        all_data = response_all.json()

        # Request with offset=1&limit=10, should skip the first item
        response = await client.get(
            "/graph/nodes/test-tag/resources?offset=1&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 3  # Total matching resources
        assert len(data["items"]) == 2  # 2 remaining after skipping first
        assert data["limit"] == 10
        assert data["offset"] == 1

        # Verify that the first item from all results is skipped
        assert data["items"][0]["id"] == all_data["items"][1]["id"]
        assert data["items"][1]["id"] == all_data["items"][2]["id"]

    async def test_get_node_resources_limit_too_high(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test that limit=101 returns 422 validation error."""
        response = await client.get(
            "/graph/nodes/test-tag/resources?limit=101",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_get_node_resources_limit_too_low(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test that limit=0 returns 422 validation error."""
        response = await client.get(
            "/graph/nodes/test-tag/resources?limit=0",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_get_node_resources_invalid_node_id(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test that node_id with special characters returns 422 validation error."""
        # Test with characters that would be problematic for SQL injection
        response = await client.get(
            "/graph/nodes/test%;DROP/resources",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver."""
    mock_driver = AsyncMock()
    mock_session = AsyncMock()

    @contextlib.asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_driver.get_session = lambda: mock_session_context()
    return mock_driver, mock_session


class TestGetGraph:
    """Test cases for GET /graph."""

    async def test_get_graph_all_nodes_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test successful retrieval of all graph nodes and edges."""
        mock_driver, mock_session = mock_neo4j_driver

        # Mock the graph service's get_neo4j_driver call
        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            # Mock the Neo4j query result for all nodes
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock the async iterator for records
            async def mock_records(self):
                yield {
                    "t": {"name": "AI"},
                    "t2": {"name": "Python"},
                    "r": {"weight": 3},
                }
                yield {"t": {"name": "Machine Learning"}, "t2": None, "r": None}

            mock_result.__aiter__ = mock_records

            response = await client.get("/graph", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "nodes" in data
            assert "edges" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)

            # Verify that the query was called with correct parameters
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert "owner_id" in kwargs
            assert kwargs["owner_id"] == test_user.id

    async def test_get_graph_with_root_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test successful retrieval of three-level rooted subgraph."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock the async iterator for three-level rooted graph
            # Structure: DeepLearning -> AI -> Python (parent -> current -> child)
            async def mock_records(self):
                # Root with child Python
                yield {
                    "root": {"name": "AI"},
                    "child": {"name": "Python"},
                    "r1": {"weight": 3},
                    "parent": None,
                    "r2": None,
                }
                # Root with child Machine Learning
                yield {
                    "root": {"name": "AI"},
                    "child": {"name": "Machine Learning"},
                    "r1": {"weight": 2},
                    "parent": None,
                    "r2": None,
                }
                # Child Python with parent Deep Learning
                yield {
                    "root": {"name": "AI"},
                    "child": {"name": "Python"},
                    "r1": {"weight": 3},
                    "parent": {"name": "Deep Learning"},
                    "r2": {"weight": 4},
                }
                # Child Machine Learning with parent Neural Networks
                yield {
                    "root": {"name": "AI"},
                    "child": {"name": "Machine Learning"},
                    "r1": {"weight": 2},
                    "parent": {"name": "Neural Networks"},
                    "r2": {"weight": 1},
                }

            mock_result.__aiter__ = mock_records

            response = await client.get("/graph?root=AI", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "nodes" in data
            assert "edges" in data

            # Verify three-level structure
            node_levels = {node["id"]: node["level"] for node in data["nodes"]}

            # Root node should be "current"
            assert "AI" in node_levels
            assert node_levels["AI"] == "current"

            # Direct neighbors should be "child"
            assert "Python" in node_levels
            assert node_levels["Python"] == "child"
            assert "Machine Learning" in node_levels
            assert node_levels["Machine Learning"] == "child"

            # Neighbors of neighbors should be "parent"
            assert "Deep Learning" in node_levels
            assert node_levels["Deep Learning"] == "parent"
            assert "Neural Networks" in node_levels
            assert node_levels["Neural Networks"] == "parent"

            # Should have edges between all levels
            assert len(data["edges"]) >= 2  # At least root-child and child-parent edges

            # Verify the query was called with root parameter
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert "root" in kwargs
            assert kwargs["root"] == "AI"
            assert kwargs["owner_id"] == test_user.id

    async def test_get_graph_empty_result(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test retrieval when user has no tags."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock empty result
            async def mock_records(self):
                return
                yield  # No records

            mock_result.__aiter__ = mock_records

            response = await client.get("/graph", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["nodes"] == []
            assert data["edges"] == []

    async def test_get_graph_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/graph")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_graph_with_nonexistent_root(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test retrieval with a root tag that doesn't exist."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock empty result for nonexistent root
            async def mock_records(self):
                return
                yield  # No records

            mock_result.__aiter__ = mock_records

            response = await client.get(
                "/graph?root=NonexistentTag", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["nodes"] == []
            assert data["edges"] == []

            # Verify the query was called with the nonexistent root
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert kwargs["root"] == "NonexistentTag"


class TestExpandGraph:
    """Test cases for POST /graph/expand."""

    async def test_expand_graph_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test successful expansion of a graph node with neighbors."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock the async iterator for expand query result
            async def mock_records(self):
                yield {
                    "root": {"name": "AI"},
                    "neighbor": {"name": "Python"},
                    "r": {"weight": 3},
                }
                yield {
                    "root": {"name": "AI"},
                    "neighbor": {"name": "Machine Learning"},
                    "r": {"weight": 2},
                }

            mock_result.__aiter__ = mock_records

            response = await client.post(
                "/graph/expand",
                headers=auth_headers,
                json={"node_id": "AI", "direction": "out"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "nodes" in data
            assert "edges" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)

            # Check that child nodes are returned
            node_ids = [node["id"] for node in data["nodes"]]
            assert "Python" in node_ids
            assert "Machine Learning" in node_ids

            # Check that all nodes have level "child"
            for node in data["nodes"]:
                assert node["level"] == "child"

            # Check that edges are from AI to children
            assert len(data["edges"]) == 2
            for edge in data["edges"]:
                assert edge["source"] == "AI"
                assert edge["target"] in ["Python", "Machine Learning"]
                assert edge["weight"] in [2, 3]

            # Verify the query was called with correct parameters
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert "node_id" in kwargs
            assert kwargs["node_id"] == "AI"
            assert kwargs["owner_id"] == test_user.id

    async def test_expand_graph_no_neighbors(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test expansion of a node with no neighbors returns empty response."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock empty result (no neighbors)
            async def mock_records(self):
                return
                yield  # No records

            mock_result.__aiter__ = mock_records

            response = await client.post(
                "/graph/expand",
                headers=auth_headers,
                json={"node_id": "IsolatedTag", "direction": "out"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["nodes"] == []
            assert data["edges"] == []

            # Verify the query was called
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert kwargs["node_id"] == "IsolatedTag"
            assert kwargs["owner_id"] == test_user.id

    async def test_expand_graph_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.post(
            "/graph/expand",
            json={"node_id": "AI", "direction": "out"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expand_graph_direction_in(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test expansion with direction='in' uses inbound query."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock the async iterator for expand query result
            async def mock_records(self):
                yield {
                    "root": {"name": "AI"},
                    "neighbor": {"name": "DeepLearning"},
                    "r": {"weight": 5},
                }

            mock_result.__aiter__ = mock_records

            response = await client.post(
                "/graph/expand",
                headers=auth_headers,
                json={"node_id": "AI", "direction": "in"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check that child nodes are returned
            assert len(data["nodes"]) == 1
            assert data["nodes"][0]["id"] == "DeepLearning"
            assert data["nodes"][0]["level"] == "child"

            # Check that edges are from AI to children
            assert len(data["edges"]) == 1
            assert data["edges"][0]["source"] == "AI"
            assert data["edges"][0]["target"] == "DeepLearning"

            # Verify that inbound query was used (check for <- in query)
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            query = args[0]
            assert "<-[r:RELATED_TO]-" in query

    async def test_expand_graph_direction_both(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_neo4j_driver,
    ):
        """Test expansion with direction='both' uses undirected query."""
        mock_driver, mock_session = mock_neo4j_driver

        with patch("services.graph_service.get_neo4j_driver", return_value=mock_driver):
            mock_result = AsyncMock()
            mock_session.run.return_value = mock_result

            # Mock the async iterator for expand query result
            async def mock_records(self):
                yield {
                    "root": {"name": "AI"},
                    "neighbor": {"name": "Python"},
                    "r": {"weight": 3},
                }
                yield {
                    "root": {"name": "AI"},
                    "neighbor": {"name": "DeepLearning"},
                    "r": {"weight": 5},
                }

            mock_result.__aiter__ = mock_records

            response = await client.post(
                "/graph/expand",
                headers=auth_headers,
                json={"node_id": "AI", "direction": "both"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check that child nodes are returned
            assert len(data["nodes"]) == 2
            node_ids = [node["id"] for node in data["nodes"]]
            assert "Python" in node_ids
            assert "DeepLearning" in node_ids

            # Check that edges are from AI to children
            assert len(data["edges"]) == 2

            # Verify that bidirectional query was used (check for - without arrow)
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            query = args[0]
            assert "-[r:RELATED_TO]-" in query
            # Ensure it's not specifically directional
            assert "->" not in query
            assert "<-" not in query

    async def test_expand_graph_invalid_direction(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test expansion with invalid direction returns 422."""
        response = await client.post(
            "/graph/expand",
            headers=auth_headers,
            json={"node_id": "AI", "direction": "sideways"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
