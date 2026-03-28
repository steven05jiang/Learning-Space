"""Tests for the agent service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from models.user import User
from schemas.agent import AgentQuery, AgentResponse, ConversationMessage
from services.agent_service import AgentService


class TestAgentService:
    """Test cases for AgentService."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def agent_service(self):
        """Create an AgentService instance."""
        return AgentService()

    @pytest.fixture
    async def agent_service_with_mocked_llm(self, agent_service):
        """Create an AgentService with mocked LLM components."""
        with patch("services.agent_service.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.anthropic_model = "claude-haiku-4-5-20251001"

            with patch("services.agent_service.get_llm_client") as mock_get_client:
                mock_llm = Mock()
                mock_get_client.return_value = mock_llm
                agent_service.llm = mock_llm

                # Mock the graph compilation
                with patch("services.agent_service.StateGraph") as mock_state_graph:
                    mock_workflow = Mock()
                    mock_state_graph.return_value = mock_workflow

                    mock_graph = Mock()
                    mock_workflow.compile.return_value = mock_graph
                    agent_service.graph = mock_graph
                    agent_service._initialized = True

                    yield agent_service

    async def test_initialization_without_api_key(self, agent_service):
        """Test initialization without API key."""
        with patch("services.agent_service.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = ""

            await agent_service._initialize()

            assert agent_service.llm is None
            assert agent_service.graph is None
            assert agent_service._initialized is False

    async def test_initialization_with_test_key(self, agent_service):
        """Test initialization with test API key."""
        with patch("services.agent_service.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = "test-anthropic-key-for-development"

            await agent_service._initialize()

            assert agent_service.llm is None
            assert agent_service.graph is None
            assert agent_service._initialized is False

    async def test_initialization_with_valid_key(self, agent_service):
        """Test successful initialization with valid API key."""
        with patch("services.agent_service.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = "valid-key"
            mock_settings.anthropic_model = "claude-haiku-4-5-20251001"

            with patch("services.agent_service.get_llm_client") as mock_get_client:
                mock_llm = Mock()
                mock_get_client.return_value = mock_llm

                with patch.object(agent_service, "_build_graph") as mock_build_graph:
                    await agent_service._initialize()

                    assert agent_service.llm == mock_llm
                    assert agent_service._initialized is True
                    mock_build_graph.assert_called_once()

    async def test_query_without_initialization(self, agent_service, mock_user):
        """Test query when agent is not initialized."""
        # Ensure agent is not initialized by patching settings during query
        with patch("services.agent_service.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = ""

            # Ensure agent is not initialized
            agent_service._initialized = False
            agent_service.llm = None
            agent_service.graph = None

            query = AgentQuery(query="What resources do I have?")

            response = await agent_service.query(mock_user, query)

            assert isinstance(response, AgentResponse)
            assert "not available" in response.response
            assert response.sources is None

    async def test_query_with_empty_conversation_history(
        self, agent_service_with_mocked_llm, mock_user
    ):
        """Test query with no conversation history."""
        query = AgentQuery(query="What resources do I have about Python?")

        # Mock the graph execution
        mock_final_state = {
            "messages": [Mock(content="I found 3 resources about Python.")],
            "tool_results": [],
        }
        agent_service_with_mocked_llm.graph.ainvoke = AsyncMock(
            return_value=mock_final_state
        )

        response = await agent_service_with_mocked_llm.query(mock_user, query)

        assert isinstance(response, AgentResponse)
        assert "Python" in response.response
        assert response.sources is None

    async def test_query_with_conversation_history(
        self, agent_service_with_mocked_llm, mock_user
    ):
        """Test query with conversation history."""
        conversation_history = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(
                role="assistant", content="Hi! How can I help you today?"
            ),
        ]
        query = AgentQuery(
            query="Tell me about my machine learning resources",
            conversation_history=conversation_history,
        )

        # Mock the graph execution
        mock_final_state = {
            "messages": [Mock(content="You have 5 machine learning resources.")],
            "tool_results": [
                {"tool": "search_resources", "results": ["resource1", "resource2"]}
            ],
        }
        agent_service_with_mocked_llm.graph.ainvoke = AsyncMock(
            return_value=mock_final_state
        )

        response = await agent_service_with_mocked_llm.query(mock_user, query)

        assert isinstance(response, AgentResponse)
        assert "machine learning" in response.response
        assert response.sources is not None

    async def test_query_handles_exception(
        self, agent_service_with_mocked_llm, mock_user
    ):
        """Test query handles exceptions gracefully."""
        query = AgentQuery(query="What resources do I have?")

        # Mock the graph execution to raise an exception
        agent_service_with_mocked_llm.graph.ainvoke = AsyncMock(
            side_effect=Exception("Graph execution failed")
        )

        response = await agent_service_with_mocked_llm.query(mock_user, query)

        assert isinstance(response, AgentResponse)
        assert "error" in response.response.lower()
        assert response.sources is None

    @pytest.mark.asyncio
    async def test_search_resources_tool(self, agent_service):
        """Test the search_resources tool functionality."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            # Mock async generator for database session
            async def mock_generator():
                yield AsyncMock()

            mock_get_db.return_value = mock_generator()

            # Mock the ResourceSearchService
            with patch(
                "services.agent_service.resource_search_service"
            ) as mock_service:
                # Create mock search result using the actual classes
                from datetime import UTC, datetime

                from services.resource_search_service import (
                    ResourceSearchItem,
                    SearchResult,
                )

                mock_item = ResourceSearchItem(
                    id="1",
                    title="Python Guide",
                    summary="A comprehensive Python guide",
                    tags=["python", "programming"],
                    top_level_categories=["Technology"],
                    original_content="https://example.com/python-guide",
                    content_type="url",
                    status="READY",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    rank=0.9,
                )

                mock_service.search = AsyncMock(
                    return_value=SearchResult(resources=[mock_item], total=1)
                )

                tool = agent_service._search_resources_tool
                result = await tool.coroutine("Python")

                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0]["id"] == "1"
                assert result[0]["title"] == "Python Guide"
                assert result[0]["url"] == "https://example.com/python-guide"

    @pytest.mark.asyncio
    async def test_search_resources_tool_exception(self, agent_service):
        """Test the search_resources tool handles exceptions."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            tool = agent_service._search_resources_tool

            with pytest.raises(Exception) as exc_info:
                await tool.coroutine("Python")

            assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_graph_context_tool(self, agent_service):
        """Test the get_graph_context tool wrapper."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch.object(agent_service, "_get_graph_context") as mock_context:
            mock_context.return_value = {
                "root_tag": "python",
                "related_nodes": ["machine-learning", "web-development"],
                "connections": 3,
            }

            result = await agent_service._get_graph_context_wrapper("python")

            assert "Graph context for 'python'" in result
            assert "machine-learning" in result

    @pytest.mark.asyncio
    async def test_get_graph_context_tool_exception(self, agent_service):
        """Test the get_graph_context tool handles exceptions."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch.object(agent_service, "_get_graph_context") as mock_context:
            mock_context.side_effect = Exception("Graph service failed")

            result = await agent_service._get_graph_context_wrapper("python")

            assert "Error getting graph context" in result
            assert "Graph service failed" in result

    @pytest.mark.asyncio
    async def test_get_resource_detail_tool(self, agent_service):
        """Test the get_resource_detail tool wrapper."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            # Mock async generator for database session
            async def mock_generator():
                yield AsyncMock()

            mock_get_db.return_value = mock_generator()

            with patch.object(agent_service, "_get_resource_detail") as mock_detail:
                mock_detail.return_value = {
                    "id": "123",
                    "title": "Python Tutorial",
                    "summary": "Complete Python guide",
                }

                result = await agent_service._get_resource_detail_wrapper("123")

                assert result is not None
                assert "Resource details" in result
                assert "Python Tutorial" in result

    @pytest.mark.asyncio
    async def test_get_resource_detail_tool_not_found(self, agent_service):
        """Test the get_resource_detail tool when resource not found."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            # Mock async generator for database session
            async def mock_generator():
                yield AsyncMock()

            mock_get_db.return_value = mock_generator()

            with patch.object(agent_service, "_get_resource_detail") as mock_detail:
                mock_detail.return_value = None

                result = await agent_service._get_resource_detail_wrapper("999")

                assert result is not None
                assert "Resource 999 not found" in result

    @pytest.mark.asyncio
    async def test_get_resource_detail_tool_exception(self, agent_service):
        """Test the get_resource_detail tool handles exceptions."""
        # Set user context for security fix
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            result = await agent_service._get_resource_detail_wrapper("123")

            assert "Error getting resource detail" in result
            assert "Database error" in result

    async def test_search_resources_tool_integration(self, agent_service):
        """Test the search_resources tool calls ResourceSearchService correctly."""
        # Set user context
        agent_service._current_user_id = 1

        with patch("services.agent_service.get_db") as mock_get_db:
            # Mock database session
            mock_db = AsyncMock()

            async def mock_generator():
                yield mock_db

            mock_get_db.return_value = mock_generator()

            with patch(
                "services.agent_service.resource_search_service"
            ) as mock_service:
                # Create mock search result
                from datetime import UTC, datetime

                from services.resource_search_service import (
                    ResourceSearchItem,
                    SearchResult,
                )

                mock_items = [
                    ResourceSearchItem(
                        id="1",
                        title="Python Guide",
                        summary="Learn Python programming",
                        tags=["python", "programming"],
                        top_level_categories=["Technology"],
                        original_content="Python tutorial content",
                        content_type="text",
                        status="READY",
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                        rank=0.9,
                    ),
                    ResourceSearchItem(
                        id="2",
                        title="Python Web Framework",
                        summary="Django tutorial",
                        tags=["python", "django", "web"],
                        top_level_categories=["Technology"],
                        original_content="https://example.com/django",
                        content_type="url",
                        status="READY",
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                        rank=0.8,
                    ),
                ]

                # Mock the async search method with call tracking
                mock_service.search = AsyncMock(
                    return_value=SearchResult(resources=mock_items, total=2)
                )

                tool = agent_service._search_resources_tool
                result = await tool.coroutine("Python", tag="programming")

                # Verify the service was called correctly
                mock_service.search.assert_called_once_with(
                    session=mock_db,
                    owner_id=1,
                    query="Python",
                    tag="programming",
                    limit=10,
                    offset=0,
                )

                # Check the results
                assert len(result) == 2
                assert result[0]["title"] == "Python Guide"
                assert result[0]["tags"] == ["python", "programming"]
                assert result[0]["url"] is None  # text content
                assert result[1]["url"] == "https://example.com/django"  # url content

    async def test_get_graph_context_implementation(self, agent_service):
        """Test the _get_graph_context implementation."""
        with patch("services.agent_service.graph_service") as mock_graph_service:
            # Mock graph service responses as async functions
            mock_graph_service.get_graph = AsyncMock(
                return_value={
                    "nodes": [
                        {"id": "python", "label": "python"},
                        {"id": "machine-learning", "label": "machine-learning"},
                    ],
                    "edges": [
                        {"source": "python", "target": "machine-learning", "weight": 5}
                    ],
                }
            )

            mock_graph_service.get_neighbors = AsyncMock(
                return_value={
                    "nodes": [{"id": "web-development", "label": "web-development"}],
                    "edges": [],
                }
            )

            result = await agent_service._get_graph_context(1, "python")

            assert result["root_tag"] == "python"
            assert "machine-learning" in result["related_nodes"]
            assert result["connections"] == 1
            assert "web-development" in result["neighbors"]

    async def test_get_resource_detail_implementation(self, agent_service):
        """Test the _get_resource_detail implementation."""
        mock_db = AsyncMock()

        # Create mock resource
        mock_resource = Mock()
        mock_resource.id = 123
        mock_resource.title = "Python Tutorial"
        mock_resource.summary = "Complete Python guide"
        mock_resource.original_content = "Tutorial content here"
        mock_resource.content_type = "text"
        mock_resource.tags = ["python", "tutorial"]
        mock_resource.status = "READY"
        mock_resource.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        mock_db.execute.return_value = mock_result

        result = await agent_service._get_resource_detail(mock_db, 1, "123")

        assert result is not None
        assert result["id"] == "123"
        assert result["title"] == "Python Tutorial"
        assert result["content_type"] == "text"
        assert result["tags"] == ["python", "tutorial"]

    async def test_get_resource_detail_invalid_id(self, agent_service):
        """Test _get_resource_detail with invalid resource ID."""
        mock_db = AsyncMock()

        result = await agent_service._get_resource_detail(mock_db, 1, "invalid")

        assert result is None

    async def test_get_resource_detail_not_found(self, agent_service):
        """Test _get_resource_detail when resource not found."""
        mock_db = AsyncMock()

        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await agent_service._get_resource_detail(mock_db, 1, "999")

        assert result is None

    def test_should_continue_with_tool_calls(self, agent_service):
        """Test _should_continue when message has tool calls."""
        mock_message = Mock()
        mock_message.tool_calls = [
            {"name": "search_resources", "args": {"query": "test"}}
        ]

        state = {"messages": [mock_message]}
        result = agent_service._should_continue(state)

        assert result == "tools"

    def test_should_continue_without_tool_calls(self, agent_service):
        """Test _should_continue when message has no tool calls."""
        mock_message = Mock()
        mock_message.tool_calls = []

        state = {"messages": [mock_message]}
        result = agent_service._should_continue(state)

        assert result == "end"

    def test_should_continue_no_tool_calls_attribute(self, agent_service):
        """Test _should_continue when message has no tool_calls attribute."""
        mock_message = Mock(spec=[])  # Mock without tool_calls attribute

        state = {"messages": [mock_message]}
        result = agent_service._should_continue(state)

        assert result == "end"

    async def test_user_context_management(
        self, agent_service_with_mocked_llm, mock_user
    ):
        """Test that user context is properly set and reset."""
        query = AgentQuery(query="Test query")

        # Mock the graph execution
        mock_final_state = {
            "messages": [Mock(content="Test response")],
            "tool_results": [],
        }
        agent_service_with_mocked_llm.graph.ainvoke = AsyncMock(
            return_value=mock_final_state
        )

        # Verify user ID is None before query
        assert agent_service_with_mocked_llm._current_user_id is None

        await agent_service_with_mocked_llm.query(mock_user, query)

        # Verify user ID is reset after query
        assert agent_service_with_mocked_llm._current_user_id is None


class TestAgentSchemas:
    """Test the agent-related Pydantic schemas."""

    def test_conversation_message_validation(self):
        """Test ConversationMessage validation."""
        # Valid message
        msg = ConversationMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

        # Valid assistant message
        msg = ConversationMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_conversation_message_invalid_role(self):
        """Test ConversationMessage with invalid role."""
        with pytest.raises(ValueError, match="role must be 'user' or 'assistant'"):
            ConversationMessage(role="system", content="Hello")

    def test_conversation_message_empty_content(self):
        """Test ConversationMessage with empty content."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            ConversationMessage(role="user", content="")

        with pytest.raises(ValueError, match="content cannot be empty"):
            ConversationMessage(role="user", content="   ")

    def test_conversation_message_content_stripping(self):
        """Test that content is properly stripped."""
        msg = ConversationMessage(role="user", content="  Hello World  ")
        assert msg.content == "Hello World"

    def test_agent_query_validation(self):
        """Test AgentQuery validation."""
        # Simple query
        query = AgentQuery(query="What resources do I have?")
        assert query.query == "What resources do I have?"
        assert query.conversation_history == []

        # Query with history
        history = [ConversationMessage(role="user", content="Hello")]
        query = AgentQuery(query="Follow up question", conversation_history=history)
        assert len(query.conversation_history) == 1

    def test_agent_query_empty_query(self):
        """Test AgentQuery with empty query."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            AgentQuery(query="")

        with pytest.raises(ValueError, match="query cannot be empty"):
            AgentQuery(query="   ")

    def test_agent_query_query_stripping(self):
        """Test that query is properly stripped."""
        query = AgentQuery(query="  What are my resources?  ")
        assert query.query == "What are my resources?"

    def test_agent_response_creation(self):
        """Test AgentResponse creation."""
        # Simple response
        response = AgentResponse(response="Here are your resources...")
        assert response.response == "Here are your resources..."
        assert response.sources is None

        # Response with sources
        sources = [{"tool": "search", "results": ["res1", "res2"]}]
        response = AgentResponse(response="Found resources", sources=sources)
        assert response.response == "Found resources"
        assert response.sources == sources
