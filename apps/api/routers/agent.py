"""Agent endpoints for conversational resource queries."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from core.deps import get_current_user
from models.user import User
from schemas.agent import AgentQuery, AgentResponse
from services.agent_service import AgentService, get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    agent_query: AgentQuery,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Query the conversational agent about your resources.

    - **query**: Your question or request
    - **conversation_history**: Previous messages in the conversation (optional)

    The agent can:
    - Search through your saved resources by content, title, or tags
    - Explore relationships between topics in your knowledge graph
    - Provide detailed information about specific resources

    Returns an AI-generated response based on your resources and conversation context.
    """
    try:
        response = await agent_service.query(current_user, agent_query)
        return response
    except Exception as e:
        logger.error(
            f"Error querying agent for user {current_user.id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your query",
        )
