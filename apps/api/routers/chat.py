"""Chat endpoints for stateful conversational queries."""

import json
import logging
import uuid
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from models.conversation import Conversation, Message, MessageRole
from models.database import AsyncSessionLocal, get_db
from models.user import User
from schemas.agent import AgentQuery, ConversationMessage
from schemas.chat import ChatRequest, ChatResponse
from schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    ConversationWithMessagesResponse,
    MessageResponse,
)
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
                    detail="Conversation not found",
                )

            if conversation.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to conversation",
                )
        else:
            # Create new conversation
            conversation = Conversation(id=uuid.uuid4(), user_id=user_id, title=None)
            db.add(conversation)
            await db.flush()  # Ensure conversation has an ID

        # Step 4: Persist user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message,
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
                    ConversationMessage(role=msg.role.value, content=msg.content)
                )

        # Build agent query
        agent_query = AgentQuery(
            query=request.message, conversation_history=conversation_history
        )

        # Step 7: Call agent service
        agent_response = await agent_service.query(current_user, agent_query)

        # Step 8: Persist assistant message
        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=agent_response.response,
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
            role="assistant",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing chat for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message",
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """SSE endpoint — streams agent progress then final response.

    Event format (text/event-stream):
      data: {"type": "progress", "content": "...", "conversation_id": "..."}
      data: {"type": "response", "content": "...", "conversation_id": "..."}
      data: [DONE]
    """
    user_id = current_user.id

    try:
        # Load or create conversation (same as /chat)
        if request.conversation_id:
            result = await db.execute(
                select(Conversation).where(Conversation.id == request.conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            if conversation.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            conversation = Conversation(id=uuid.uuid4(), user_id=user_id, title=None)
            db.add(conversation)
            await db.flush()

        # Persist user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message,
        )
        db.add(user_message)
        await db.flush()

        await db.commit()

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error setting up stream for user %s: %s", user_id, e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start stream")

    agent_query = AgentQuery(query=request.message, conversation_history=[])
    conversation_id = conversation.id
    final_response: dict = {"content": ""}

    async def generate():
        try:
            async for event in agent_service.stream_query(current_user, agent_query):
                if event["type"] == "response":
                    final_response["content"] = event["content"]
                payload = json.dumps({**event, "conversation_id": str(conversation_id)})
                yield f"data: {payload}\n\n"
        except Exception as e:
            logger.error("Error during stream generation: %s", e, exc_info=True)
            payload = json.dumps({"type": "error", "content": "Stream error", "conversation_id": str(conversation_id)})
            yield f"data: {payload}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    async def persist_response():
        """Save assistant message after streaming completes."""
        try:
            async with AsyncSessionLocal() as session:
                assistant_msg = Message(
                    id=uuid.uuid4(),
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=final_response["content"],
                )
                session.add(assistant_msg)
                conv = await session.get(Conversation, conversation_id)
                if conv:
                    conv.updated_at = datetime.utcnow()
                await session.commit()
        except Exception as e:
            logger.error("Failed to persist assistant message: %s", e, exc_info=True)

    background_tasks.add_task(persist_response)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        background=background_tasks,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    Get a paginated list of the current user's conversations.

    - **limit**: Number of conversations to return (default 20, max 100)
    - **offset**: Number of conversations to skip (default 0)

    Returns conversations ordered by most recently updated first.
    """
    # Validate pagination parameters
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be at least 1",
        )
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit cannot exceed 100",
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="offset must be non-negative",
        )

    try:
        # Get total count
        count_query = select(func.count(Conversation.id)).where(
            Conversation.user_id == current_user.id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get conversations with pagination
        conversations_query = (
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        conversations_result = await db.execute(conversations_query)
        conversations = list(conversations_result.scalars().all())

        # Convert to response schemas
        conversation_responses = [
            ConversationResponse.model_validate(conv) for conv in conversations
        ]

        return ConversationListResponse(
            items=conversation_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(
            f"Error retrieving conversations for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving conversations",
        )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationWithMessagesResponse,
)
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationWithMessagesResponse:
    """
    Get a specific conversation with all its messages.

    - **conversation_id**: UUID of the conversation to retrieve

    Returns the conversation details and all messages ordered by creation time.
    """
    try:
        # Load conversation
        conversation_query = select(Conversation).where(
            Conversation.id == conversation_id
        )
        conversation_result = await db.execute(conversation_query)
        conversation = conversation_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation",
            )

        # Load all messages for the conversation
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages_result = await db.execute(messages_query)
        messages = list(messages_result.scalars().all())

        # Convert to response schemas
        message_responses = [MessageResponse.model_validate(msg) for msg in messages]

        # Build the response using conversation data and manually setting messages
        response_data = {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": message_responses,
        }

        return ConversationWithMessagesResponse(**response_data)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving conversation {conversation_id} "
            f"for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the conversation",
        )
