"""LangGraph-based conversational agent service for resource queries."""

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool, Tool, tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.agent import AgentQuery, AgentResponse, ToolCallResult
from services.graph_service import graph_service
from services.llm_client import get_llm_client
from services.resource_search_service import (
    AgentResourceResult,
    resource_search_service,
)

logger = logging.getLogger(__name__)


class _NoArgs(BaseModel):
    """Empty args schema for no-argument tools."""


SYSTEM_PROMPT = (
    "You are a helpful AI assistant for exploring and finding "
    "learning resources in the user's personal library.\n\n"
    "Search strategy:\n"
    "- Prefer broader, single-keyword queries over narrow ones.\n"
    "- If the first search returns no results, try ONE alternative "
    "keyword before giving up. Do not retry more than twice.\n\n"
    "Using the knowledge graph:\n"
    "- When calling get_graph_context, use an EXACT tag name from the search_resources "
    "results (e.g. a tag like 'python' or 'machine-learning'), not a generic topic.\n"
    "- If get_graph_context returns nothing, that is fine — skip it and move on.\n\n"
    "Responding:\n"
    "- If search_resources returned ANY results, you MUST include them in your "
    "response. Never discard found resources.\n"
    "- If nothing was found after searching, clearly say so and suggest what the user "
    "could add to their library.\n"
    "- Do not keep searching in a loop — one retry maximum, then respond.\n\n"
    "Overview questions (e.g. 'What topics am I learning about?', "
    "'What is in my library?', 'What areas am I covering?'):\n"
    "- Use list_tags to get all user-defined tags and categories — "
    "do NOT use search_resources with '*' or broad queries.\n\n"
    "Tool calling:\n"
    "- Before calling any tool, always write a brief sentence describing "
    "what you are looking up.\n"
    "- After receiving tool results, verify: do you have enough relevant "
    "information to answer the user?\n"
    "  - If yes, respond immediately.\n"
    "  - If a DIFFERENT tool would genuinely add value, call it once.\n"
    "  - Never call the same tool with the same arguments twice.\n\n"
    "Formatting:\n"
    "- Always format your entire response in Markdown.\n"
    "- Use headers, bullet lists, bold text, and code blocks where appropriate.\n"
    "- Present resource lists as Markdown bullet points with the title in bold."
)

TOOL_PROGRESS: Dict[str, str] = {
    "list_tags": "Looking up your tags and categories...",
    "search_resources": "Searching your resource library...",
    "get_graph_context": "Exploring your knowledge graph...",
    "get_resource_detail": "Fetching resource details...",
}

AGENT_MAX_SECONDS = 60
AGENT_RECURSION_LIMIT = 10


def _build_fallback(tokens: List[str], tool_results: List[dict], reason: str) -> str:
    """Build a best-effort response when the agent is interrupted."""
    partial = "".join(tokens).strip()
    if partial:
        suffix = {
            "timeout": "\n\n_(Response may be incomplete — search took too long)_",
            "max_rounds": "\n\n_(Response may be incomplete — reached search limit)_",
        }.get(reason, "")
        return partial + suffix

    if tool_results:
        items = []
        for r in tool_results[:5]:
            if isinstance(r, dict):
                title = r.get("title", "Untitled")
                summary = (r.get("summary") or "")[:120]
                entry = f"- **{title}**: {summary}" if summary else f"- **{title}**"
                items.append(entry)
        prefix = {
            "timeout": "I ran out of time, but here's what I found:\n\n",
            "max_rounds": "I reached my search limit, but here's what I found:\n\n",
        }.get(reason, "Here's what I found:\n\n")
        return prefix + "\n".join(items)

    return {
        "timeout": (
            "I'm sorry, the search took too long. "
            "Try a more specific question or check back in a moment."
        ),
        "max_rounds": (
            "I'm sorry, I couldn't complete the search within the allowed steps. "
            "Try rephrasing with a simpler, more specific question."
        ),
        "no_response": (
            "I couldn't find a relevant answer. "
            "Try rephrasing your question or adding more resources to your library."
        ),
    }.get(reason, "I'm sorry, I couldn't complete your request. Please try again.")


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
        self._current_user_id = None  # Store current user ID for tool calls

    async def _initialize(self):
        """Initialize the LLM and graph components."""
        if self._initialized:
            return

        # Check for test key - this applies to all providers for consistency
        provider_key = getattr(settings, f"{settings.llm_provider}_api_key", "")
        if not provider_key or provider_key == "test-anthropic-key-for-development":
            logger.warning(
                f"LLM provider '{settings.llm_provider}' API key not configured - "
                "agent will not work"
            )
            self._initialized = False
            return

        try:
            # Initialize the LLM using the factory
            self.llm = get_llm_client()
        except ValueError as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
            self._initialized = False
            return

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

        # Compile without checkpointer — conversation history is managed by the DB.
        # MemorySaver + DB-loaded history caused double-accumulation of messages,
        # growing context to 400K+ tokens per request and starving the model
        # of output budget.
        self.graph = workflow.compile()

    async def _create_tools(self) -> List:
        """Create the tools available to the agent."""
        return [
            StructuredTool(
                name="list_tags",
                description=(
                    "Return all tags and categories the user has applied to their "
                    "resources. Use for any broad overview question about what the "
                    "user is learning, exploring, or has saved — topics, areas, "
                    "domains, subjects, themes. "
                    "Examples: 'What topics am I learning about?', "
                    "'What areas do I have resources in?', "
                    "'What domains am I covering?', 'What is in my library?'. "
                    "Do NOT use search_resources with '*' or broad queries."
                ),
                args_schema=_NoArgs,
                func=lambda: None,
                coroutine=self._list_tags_wrapper,
            ),
            self._search_resources_tool,
            Tool(
                name="get_graph_context",
                description=(
                    "Get related tags and concepts from the user's knowledge graph. "
                    "IMPORTANT: the 'tag' argument must be an EXACT tag string "
                    "returned by search_resources (e.g. 'python', 'machine-learning'). "
                    "Do not pass generic topic names. "
                    "Use this to find related tags after a successful search."
                ),
                func=lambda tag: None,
                coroutine=self._get_graph_context_wrapper,
            ),
            Tool(
                name="get_resource_detail",
                description=(
                    "Get full details for a specific resource by ID. "
                    "Use this to get complete information about a resource."
                ),
                func=lambda resource_id: None,
                coroutine=self._get_resource_detail_wrapper,
            ),
        ]

    @property
    def _search_resources_tool(self):
        """Create the search_resources tool with current user context."""

        @tool
        async def search_resources(
            query: str,
            tag: Optional[str] = None,
        ) -> List[dict]:
            """
            Search the user's learning resources by keyword or concept.

            Use this tool when the user asks about specific topics, technologies, or
            concepts in their library. Supports natural language queries — you do not
            need to use exact tag names.

            Args:
                query: A keyword or natural language description of what to find.
                       Examples: "LangGraph", "async Python", "machine learning basics"
                tag:   Optional. An exact tag to filter by in addition to the query.
                       Use only when the user explicitly references a tag.

            Returns:
                List of matching resources (up to 10), each with id, title, summary,
                tags, top_level_categories, and url (null for text resources).
            """
            if self._current_user_id is None:
                raise RuntimeError("Agent not initialized with user context")

            # Get database session
            async for db in get_db():
                # Call ResourceSearchService with hard limits
                logger.debug(
                    "[search_resources] query=%r tag=%r user_id=%s",
                    query,
                    tag,
                    self._current_user_id,
                )
                search_result = await resource_search_service.search(
                    session=db,
                    owner_id=self._current_user_id,
                    query=query,
                    tag=tag,
                    limit=10,
                    offset=0,
                )

                results = [
                    AgentResourceResult.from_item(r).__dict__
                    for r in search_result.resources
                ]
                logger.debug(
                    "[search_resources] returned %d results: %s",
                    len(results),
                    [r.get("title") for r in results],
                )
                return results

        return search_resources

    async def _list_tags_wrapper(self, _input: str = "") -> dict:
        """Return all tags and categories for the current user."""
        if self._current_user_id is None:
            raise RuntimeError("Agent not initialized with user context")

        async for db in get_db():
            result = await db.execute(
                select(Resource.tags, Resource.top_level_categories).where(
                    Resource.owner_id == self._current_user_id
                )
            )
            rows = result.all()

        tag_counts: Dict[str, int] = {}
        category_set: set = set()
        for tags, categories in rows:
            for t in tags or []:
                tag_counts[t] = tag_counts.get(t, 0) + 1
            for c in categories or []:
                category_set.add(c)

        sorted_tags = sorted(tag_counts, key=lambda t: -tag_counts[t])
        logger.debug(
            "[list_tags] user_id=%s tags=%d categories=%d",
            self._current_user_id,
            len(sorted_tags),
            len(category_set),
        )
        return json.dumps({"tags": sorted_tags, "categories": sorted(category_set)})

    async def _call_model(self, state: AgentState) -> Dict[str, Any]:
        """Call the model with the current state."""
        if not self.llm:
            logger.error("LLM not initialized")
            return {
                "messages": [
                    AIMessage(content="Sorry, the AI service is not available.")
                ]
            }

        logger.debug("[agent node] invoking LLM, messages=%d", len(state["messages"]))

        # Bind tools to the model
        tools = await self._create_tools()
        model_with_tools = self.llm.bind_tools(tools)

        # DeepSeek-V3 (and similar models via SiliconCloud) return content=""
        # when making tool calls. SiliconCloud rejects the next request if the
        # message history contains an AIMessage with empty string content.
        # Replace "" with " " so the payload is accepted. content=None is not
        # valid per LangChain's Pydantic schema.
        messages = [
            AIMessage(content=" ", tool_calls=m.tool_calls, id=m.id)
            if isinstance(m, AIMessage) and m.tool_calls and m.content == ""
            else m
            for m in state["messages"]
        ]

        # Call the model
        response = await model_with_tools.ainvoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                logger.debug(
                    "[agent node] tool_call: name=%s args=%s", tc["name"], tc["args"]
                )
        else:
            logger.debug("[agent node] final response (no tool calls)")

        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue with tools or end the conversation."""
        last_message = state["messages"][-1]

        # If there are tool calls, use tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, end the conversation
        return "end"

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

            messages = [SystemMessage(content=SYSTEM_PROMPT)]

            # Convert conversation history to LangChain messages
            for msg in agent_query.conversation_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

            # Add the current query
            messages.append(HumanMessage(content=agent_query.query))

            thread_id = f"user_{user.id}_conversation"
            config = {"recursion_limit": AGENT_RECURSION_LIMIT}

            # Wrap graph invocation in a root span so Phoenix session view shows
            # the user query as input and assistant response as output.
            from opentelemetry import context as otel_context
            from opentelemetry import trace as otel_trace

            tracer = otel_trace.get_tracer(__name__)
            # Start as a new root span (detached from the HTTP request span) so
            # Phoenix shows it as a standalone AGENT trace, not nested under POST /chat.
            with tracer.start_as_current_span(
                "agent.query",
                context=otel_context.Context(),
            ) as span:
                span.set_attribute("openinference.span.kind", "AGENT")
                span.set_attribute("input.value", agent_query.query)
                span.set_attribute("session.id", thread_id)

                # Run the graph
                final_state = await self.graph.ainvoke(
                    {"messages": messages, "user_id": user.id}, config=config
                )

                # Extract the response
                last_message = final_state["messages"][-1]
                logger.debug(
                    "[agent] last_message type=%s content=%r additional_kwargs=%r",
                    type(last_message).__name__,
                    last_message.content if hasattr(last_message, "content") else "N/A",
                    getattr(last_message, "additional_kwargs", {}),
                )
                raw_content = (
                    last_message.content
                    if hasattr(last_message, "content")
                    else str(last_message)
                )
                # Handle list-format content (e.g. [{"type": "text", "text": "..."}])
                if isinstance(raw_content, list):
                    response_content = " ".join(
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in raw_content
                    ).strip()
                else:
                    response_content = raw_content

                # If model returned empty content, synthesize from tool messages
                if not response_content:
                    tool_messages = [
                        m
                        for m in final_state.get("messages", [])
                        if hasattr(m, "tool_call_id") and m.content
                    ]
                    tool_results: List[dict] = []
                    for tm in tool_messages:
                        try:
                            parsed = json.loads(tm.content)
                            if isinstance(parsed, list):
                                tool_results.extend(
                                    r for r in parsed if isinstance(r, dict)
                                )
                        except (json.JSONDecodeError, ValueError):
                            pass
                    if tool_results:
                        logger.info(
                            "[query] empty LLM content — synthesis fallback %d",
                            len(tool_results),
                        )
                        response_content = await self._synthesize_from_results(
                            agent_query.query, tool_results
                        )

                span.set_attribute("output.value", response_content)

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

    async def _synthesize_from_results(
        self, query: str, tool_results: List[dict]
    ) -> str:
        """Directly ask the LLM to summarize tool results in natural language.

        Used as a fallback when the graph completes with empty content —
        typically caused by reasoning models that consume tokens internally
        without writing to the response content field.
        """
        if not self.llm or not tool_results:
            return _build_fallback([], tool_results, "no_response")

        items = []
        for r in tool_results[:10]:
            title = r.get("title", "Untitled")
            summary = (r.get("summary") or "")[:200]
            tags = ", ".join(r.get("tags") or [])
            line = f"- **{title}**: {summary}"
            if tags:
                line += f" (tags: {tags})"
            items.append(line)

        resources_text = "\n".join(items)
        prompt = (
            f'The user asked: "{query}"\n\n'
            f"I searched their learning library and found these resources:\n\n"
            f"{resources_text}\n\n"
            f"Write a concise, helpful response that directly answers the user's "
            f"question using these resources. Mention each resource briefly."
        )

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") if isinstance(b, dict) else str(b)
                    for b in content
                ).strip()
            return content or _build_fallback([], tool_results, "no_response")
        except Exception as e:
            logger.warning("[synthesize] LLM call failed: %s", e)
            return _build_fallback([], tool_results, "no_response")

    async def stream_query(
        self, user: User, agent_query: AgentQuery
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Stream agent events: progress updates then final response.

        Yields dicts with keys:
          {"type": "progress", "content": "..."} — tool activity
          {"type": "response", "content": "..."}  — final answer
          {"type": "error",    "content": "..."}  — unrecoverable error
        """
        await self._initialize()

        if not self._initialized or not self.graph:
            yield {
                "type": "response",
                "content": (
                    "Sorry, the AI agent is not available. "
                    "Please check the configuration."
                ),
            }
            return

        self._current_user_id = user.id
        config = {"recursion_limit": AGENT_RECURSION_LIMIT}

        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in agent_query.conversation_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=agent_query.query))

        current_tokens: List[str] = []
        collected_tool_results: List[dict] = []
        start_time = time.monotonic()

        try:
            async for event in self.graph.astream_events(
                {"messages": messages, "user_id": user.id},
                config=config,
                version="v2",
            ):
                # Hard timeout check
                if time.monotonic() - start_time > AGENT_MAX_SECONDS:
                    logger.warning(
                        "[stream_query] timeout after %ds", AGENT_MAX_SECONDS
                    )
                    yield {
                        "type": "response",
                        "content": _build_fallback(
                            current_tokens, collected_tool_results, "timeout"
                        ),
                    }
                    return

                event_name = event.get("event", "")

                if event_name == "on_tool_start":
                    tool_name = event.get("name", "")
                    current_tokens = []  # reset — this LLM turn was for tool planning
                    progress = TOOL_PROGRESS.get(tool_name, "Working on it...")
                    logger.debug("[stream_query] tool_start name=%s", tool_name)
                    yield {"type": "progress", "content": progress}

                elif event_name == "on_tool_end":
                    tool_name = event.get("name", "")
                    output = event.get("data", {}).get("output")
                    results: List[dict] = []
                    if isinstance(output, list):
                        results = [r for r in output if isinstance(r, dict)]
                    elif isinstance(output, str):
                        try:
                            parsed = json.loads(output)
                            if isinstance(parsed, list):
                                results = [r for r in parsed if isinstance(r, dict)]
                        except (json.JSONDecodeError, ValueError):
                            pass
                    collected_tool_results.extend(results)
                    logger.debug(
                        "[stream_query] tool_end name=%s results=%d total=%d",
                        tool_name,
                        len(results),
                        len(collected_tool_results),
                    )

                elif event_name == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        if isinstance(content, str) and content:
                            current_tokens.append(content)
                        elif isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and (
                                    block.get("type") == "text"
                                ):
                                    current_tokens.append(block.get("text", ""))

            # Graph completed normally
            response = "".join(current_tokens).strip()
            if not response and collected_tool_results:
                logger.info(
                    "[stream_query] empty LLM content, %d results — synthesis fallback",
                    len(collected_tool_results),
                )
                yield {"type": "progress", "content": "Summarizing results..."}
                response = await self._synthesize_from_results(
                    agent_query.query, collected_tool_results
                )
            if not response:
                response = _build_fallback([], collected_tool_results, "no_response")
            yield {"type": "response", "content": response}

        except Exception as e:
            err_type = type(e).__name__
            if "GraphRecursionError" in err_type or "recursion" in str(e).lower():
                logger.warning("[stream_query] recursion limit hit")
                yield {
                    "type": "response",
                    "content": _build_fallback(
                        current_tokens, collected_tool_results, "max_rounds"
                    ),
                }
            else:
                logger.error("[stream_query] unexpected error: %s", e, exc_info=True)
                yield {
                    "type": "error",
                    "content": "Sorry, I encountered an error. Please try again.",
                }
        finally:
            self._current_user_id = None


# Global instance
agent_service = AgentService()


async def get_agent_service() -> AgentService:
    """Dependency function to get the agent service."""
    return agent_service
