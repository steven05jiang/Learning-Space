"""Chat endpoints for stateful conversational queries."""

import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.conversation import Conversation, Message, MessageRole
from models.database import get_db
from models.user import User
from schemas.agent import AgentQuery, ConversationMessage
from schemas.chat import ChatRequest, ChatResponse
from services.agent_service import AgentService, get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """
    Send a message in a chat conversation.

    - **message**: Your message (required, max 2000 characters)
    - **conversation_id**: Continue existing conversation (optional,
      creates new if omitted)

    If conversation_id is provided, the conversation must belong to the current user.
    The endpoint persists both the user message and assistant response to the database.
    """
    # Capture user ID early to avoid SQLAlchemy issues in error handling
    user_id = current_user.id

    try:
        # Step 2-3: Load or create conversation
        if request.conversation_id:
            # Load existing conversation
            conversation_query = select(Conversation).where(
                Conversation.id == request.conversation_id
            )
            result = await db.execute(conversation_query)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )

            if conversation.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to conversation"
                )
        else:
            # Create new conversation
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                title=None
            )
            db.add(conversation)
            await db.flush()  # Ensure conversation has an ID

        # Step 4: Persist user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message
        )
        db.add(user_message)
        await db.flush()  # Ensure message is persisted before querying history

        # Step 5: Load full message history for this conversation
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        messages_result = await db.execute(messages_query)
        all_messages: List[Message] = list(messages_result.scalars().all())

        # Step 6: Build conversation history for agent (excluding current user message)
        conversation_history = []
        for msg in all_messages:
            # Exclude current user message to avoid duplication
            if msg.id != user_message.id:
                conversation_history.append(
                    ConversationMessage(
                        role=msg.role.value,
                        content=msg.content
                    )
                )

        # Build agent query
        agent_query = AgentQuery(
            query=request.message,
            conversation_history=conversation_history
        )

        # Step 7: Call agent service
        agent_response = await agent_service.query(current_user, agent_query)

        # Step 8: Persist assistant message
        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=agent_response.response
        )
        db.add(assistant_message)

        # Step 9: Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        # Commit all changes
        await db.commit()

        # Step 10: Return response
        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            response=agent_response.response,
            role="assistant"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Error processing chat for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        )
