"""LangGraph-based conversational agent service for resource queries."""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.agent import AgentQuery, AgentResponse, ToolCallResult
from services.graph_service import graph_service

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    """State for the agent graph, extending the basic MessagesState."""

    tool_results: List[ToolCallResult] = []
    user_id: Optional[int] = None


class AgentService:
    """LangGraph-based conversational agent for user resource queries."""

    def __init__(self):
        """Initialize the agent service with LLM and tools."""
        self.llm = None
        self.graph = None
        self._initialized = False
        self.checkpointer = MemorySaver()
        self._current_user_id = None  # Store current user ID for tool calls

    async def _initialize(self):
        """Initialize the LLM and graph components."""
        if self._initialized:
            return

        if (
            not settings.anthropic_api_key
            or settings.anthropic_api_key == "test-anthropic-key-for-development"
        ):
            logger.warning("Anthropic API key not configured - agent will not work")
            self._initialized = False
            return

        # Initialize the LLM
        self.llm = ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            temperature=0,
        )

        # Create the graph
        await self._build_graph()
        self._initialized = True

    async def _build_graph(self):
        """Build the LangGraph StateGraph with tools."""
        # Define tools
        tools = await self._create_tools()

        # Create tool node
        tool_node = ToolNode(tools)

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", tool_node)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "end": "__end__",
            },
        )
        workflow.add_edge("tools", "agent")

        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)

    async def _create_tools(self) -> List[Tool]:
        """Create the tools available to the agent."""
        return [
            Tool(
                name="search_resources",
                description=(
                    "Search user's resources by text content, title, summary, or tags. "
                    "Use this to find relevant resources based on a query."
                ),
                func=self._search_resources_wrapper,
            ),
            Tool(
                name="get_graph_context",
                description=(
                    "Get related tags and concepts from the user's knowledge graph. "
                    "Use this to explore topic relationships."
                ),
                func=self._get_graph_context_wrapper,
            ),
            Tool(
                name="get_resource_detail",
                description=(
                    "Get full details for a specific resource by ID. "
                    "Use this to get complete information about a resource."
                ),
                func=self._get_resource_detail_wrapper,
            ),
        ]

    async def _call_model(self, state: AgentState) -> Dict[str, Any]:
        """Call the model with the current state."""
        if not self.llm:
            logger.error("LLM not initialized")
            return {
                "messages": [
                    AIMessage(content="Sorry, the AI service is not available.")
                ]
            }

        # Bind tools to the model
        tools = await self._create_tools()
        model_with_tools = self.llm.bind_tools(tools)

        # Call the model
        response = await model_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue with tools or end the conversation."""
        last_message = state["messages"][-1]

        # If there are tool calls, use tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, end the conversation
        return "end"

    async def _search_resources_wrapper(self, query: str) -> str:
        """Wrapper for search_resources tool that handles database session."""
        try:
            if self._current_user_id is None:
                raise RuntimeError("Agent not initialized with user context")
            user_id = self._current_user_id
            async for db in get_db():
                result = await self._search_resources(db, user_id, query)
                return f"Found {len(result)} resources: {result}"
        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            return f"Error searching resources: {str(e)}"

    async def _search_resources(
        self, db: AsyncSession, user_id: int, query: str
    ) -> List[Dict[str, Any]]:
        """Search user's resources by content, title, summary, or tags."""
        search_term = f"%{query.lower()}%"

        # Search across title, summary, original_content, and tags
        search_query = (
            select(Resource)
            .where(
                Resource.owner_id == user_id,
                Resource.status == "READY",  # Only search ready resources
                or_(
                    func.lower(Resource.title).contains(search_term),
                    func.lower(Resource.summary).contains(search_term),
                    func.lower(Resource.original_content).contains(search_term),
                    Resource.tags.op("@>")(
                        json.dumps([query.lower()])
                    ),  # PostgreSQL contains
                ),
            )
            .limit(5)
        )  # Limit to 5 most relevant results

        result = await db.execute(search_query)
        resources = result.scalars().all()

        return [
            {
                "id": str(resource.id),
                "title": resource.title,
                "summary": resource.summary,
                "tags": resource.tags or [],
                "content_type": resource.content_type,
                "url": (
                    resource.original_content
                    if resource.content_type == "url"
                    else None
                ),
            }
            for resource in resources
        ]

    async def _get_graph_context_wrapper(self, tag: str) -> str:
        """Wrapper for get_graph_context tool."""
        try:
            if self._current_user_id is None:
                raise RuntimeError("Agent not initialized with user context")
            user_id = self._current_user_id
            result = await self._get_graph_context(user_id, tag)
            return f"Graph context for '{tag}': {result}"
        except Exception as e:
            logger.error(f"Error getting graph context: {e}")
            return f"Error getting graph context: {str(e)}"

    async def _get_graph_context(self, user_id: int, tag: str) -> Dict[str, Any]:
        """Get related tags and context from the knowledge graph."""
        # Get the graph centered around this tag
        graph_data = await graph_service.get_graph(user_id, root=tag)

        # Get neighbors for additional context
        neighbors_data = await graph_service.get_neighbors(
            user_id, tag, direction="both"
        )

        return {
            "root_tag": tag,
            "related_nodes": [
                node["id"] for node in graph_data.get("nodes", []) if node["id"] != tag
            ],
            "connections": len(graph_data.get("edges", [])),
            "neighbors": [node["id"] for node in neighbors_data.get("nodes", [])],
        }

    async def _get_resource_detail_wrapper(self, resource_id: str) -> str:
        """Wrapper for get_resource_detail tool."""
        try:
            if self._current_user_id is None:
                raise RuntimeError("Agent not initialized with user context")
            user_id = self._current_user_id
            async for db in get_db():
                result = await self._get_resource_detail(db, user_id, resource_id)
                return (
                    f"Resource details: {result}"
                    if result
                    else f"Resource {resource_id} not found"
                )
        except Exception as e:
            logger.error(f"Error getting resource detail: {e}")
            return f"Error getting resource detail: {str(e)}"

    async def _get_resource_detail(
        self, db: AsyncSession, user_id: int, resource_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get full details for a specific resource."""
        try:
            resource_id_int = int(resource_id)
        except ValueError:
            return None

        query = select(Resource).where(
            Resource.id == resource_id_int,
            Resource.owner_id == user_id,
        )

        result = await db.execute(query)
        resource = result.scalar_one_or_none()

        if not resource:
            return None

        return {
            "id": str(resource.id),
            "title": resource.title,
            "summary": resource.summary,
            "content": resource.original_content,
            "content_type": resource.content_type,
            "tags": resource.tags or [],
            "status": resource.status,
            "created_at": resource.created_at.isoformat(),
        }

    async def query(self, user: User, agent_query: AgentQuery) -> AgentResponse:
        """Process a query using the conversational agent."""
        await self._initialize()

        if not self._initialized or not self.graph:
            return AgentResponse(
                response=(
                    "Sorry, the AI agent is not available. "
                    "Please check the configuration."
                ),
                sources=None,
            )

        try:
            # Set the current user ID for tool calls
            self._current_user_id = user.id

            # Convert conversation history to LangChain messages
            messages = []
            for msg in agent_query.conversation_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

            # Add the current query
            messages.append(HumanMessage(content=agent_query.query))

            # Create a unique thread ID for this conversation
            thread_id = f"user_{user.id}_conversation"
            config = {"configurable": {"thread_id": thread_id}}

            # Run the graph
            final_state = await self.graph.ainvoke(
                {"messages": messages, "user_id": user.id}, config=config
            )

            # Extract the response
            last_message = final_state["messages"][-1]
            response_content = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

            # Extract any tool results for sources
            sources = final_state.get("tool_results", [])

            return AgentResponse(
                response=response_content,
                sources=sources if sources else None,
            )

        except Exception as e:
            logger.error(f"Error processing agent query: {e}", exc_info=True)
            return AgentResponse(
                response=(
                    "Sorry, I encountered an error while processing your query. "
                    "Please try again."
                ),
                sources=None,
            )
        finally:
            # Reset user context
            self._current_user_id = None


# Global instance
agent_service = AgentService()


async def get_agent_service() -> AgentService:
    """Dependency function to get the agent service."""
    return agent_service
