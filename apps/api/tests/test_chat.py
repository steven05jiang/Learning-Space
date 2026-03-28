"""Tests for chat endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import Conversation, Message, MessageRole
from schemas.agent import AgentResponse
from services.agent_service import get_agent_service
from tests.conftest import AsyncClient


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    @pytest.fixture
    def mock_agent_service(self):
        """Mock agent service."""
        service = AsyncMock()
        service.query.return_value = AgentResponse(
            response="Test assistant response",
            sources=None
        )
        return service

    async def test_chat_new_conversation(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        db_session: AsyncSession,
        mock_agent_service
    ):
        """Test creating a new conversation through chat."""
        user = test_user
        headers = auth_headers

        # Override the agent service dependency
        from main import app
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            response = await client.post(
                "/chat",
                json={"message": "Hello, test message"},
                headers=headers
            )
        finally:
            # Clean up dependency override
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["response"] == "Test assistant response"
        assert data["role"] == "assistant"

        # Verify conversation was created in database
        conversation_query = select(Conversation).where(
            Conversation.id == uuid.UUID(data["conversation_id"])
        )
        result = await db_session.execute(conversation_query)
        conversation = result.scalar_one_or_none()

        assert conversation is not None
        assert conversation.user_id == user.id
        assert conversation.title is None

        # Verify messages were created
        messages_query = select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.asc())
        messages_result = await db_session.execute(messages_query)
        messages = list(messages_result.scalars().all())

        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello, test message"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Test assistant response"
        assert messages[1].id == uuid.UUID(data["message_id"])

        # Verify agent service was called with correct parameters
        mock_agent_service.query.assert_called_once()
        call_args = mock_agent_service.query.call_args
        assert call_args[0][0] == user  # user argument
        agent_query = call_args[0][1]  # agent_query argument
        assert agent_query.query == "Hello, test message"
        assert agent_query.conversation_history == []

    async def test_chat_existing_conversation(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        db_session: AsyncSession,
        mock_agent_service
    ):
        """Test continuing an existing conversation."""
        user = test_user
        headers = auth_headers

        # Create an existing conversation with messages
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user.id,
            title="Existing conversation"
        )
        db_session.add(conversation)

        # Add some existing messages
        msg1 = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="First user message"
        )
        msg2 = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="First assistant response"
        )
        db_session.add(msg1)
        db_session.add(msg2)
        await db_session.commit()

        original_updated_at = conversation.updated_at

        # Override the agent service dependency
        from main import app
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            response = await client.post(
                "/chat",
                json={
                    "message": "Second user message",
                    "conversation_id": str(conversation.id)
                },
                headers=headers
            )
        finally:
            # Clean up dependency override
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert data["conversation_id"] == str(conversation.id)
        assert "message_id" in data
        assert data["response"] == "Test assistant response"

        # Refresh conversation from database to check updated_at
        await db_session.refresh(conversation)
        assert conversation.updated_at > original_updated_at

        # Verify all messages in conversation
        messages_query = select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.asc())
        messages_result = await db_session.execute(messages_query)
        messages = list(messages_result.scalars().all())

        assert len(messages) == 4  # 2 existing + 2 new
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == "Second user message"
        assert messages[3].role == MessageRole.ASSISTANT
        assert messages[3].content == "Test assistant response"

        # Verify agent service was called with conversation history
        mock_agent_service.query.assert_called_once()
        call_args = mock_agent_service.query.call_args
        agent_query = call_args[0][1]
        assert agent_query.query == "Second user message"
        assert len(agent_query.conversation_history) == 2
        assert agent_query.conversation_history[0].role == "user"
        assert agent_query.conversation_history[0].content == "First user message"
        assert agent_query.conversation_history[1].role == "assistant"
        assert agent_query.conversation_history[1].content == "First assistant response"

    async def test_chat_conversation_not_found(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        mock_agent_service
    ):
        """Test chatting with non-existent conversation ID."""
        user = test_user
        headers = auth_headers
        non_existent_id = str(uuid.uuid4())

        # Override the agent service dependency
        from main import app
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            response = await client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "conversation_id": non_existent_id
                },
                headers=headers
            )
        finally:
            # Clean up dependency override
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_chat_wrong_user_conversation(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        db_session: AsyncSession,
        mock_agent_service
    ):
        """Test accessing another user's conversation."""
        user = test_user
        headers = auth_headers

        # Create conversation for another user
        other_conversation = Conversation(
            id=uuid.uuid4(),
            user_id=999,  # Different user ID
            title="Other user's conversation"
        )
        db_session.add(other_conversation)
        await db_session.commit()

        # Override the agent service dependency
        from main import app
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            response = await client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "conversation_id": str(other_conversation.id)
                },
                headers=headers
            )
        finally:
            # Clean up dependency override
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "access denied" in response.json()["detail"].lower()

    async def test_chat_empty_message(self, client: AsyncClient, test_user, auth_headers):
        """Test validation for empty message."""
        user = test_user
        headers = auth_headers

        response = await client.post(
            "/chat",
            json={"message": ""},
            headers=headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()["detail"]
        assert any("message cannot be empty" in str(err) for err in error_detail)

    async def test_chat_message_too_long(self, client: AsyncClient, test_user, auth_headers):
        """Test validation for message exceeding character limit."""
        user = test_user
        headers = auth_headers
        long_message = "x" * 2001  # Over 2000 character limit

        response = await client.post(
            "/chat",
            json={"message": long_message},
            headers=headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()["detail"]
        assert any("cannot exceed 2000 characters" in str(err) for err in error_detail)

    async def test_chat_unauthenticated(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.post(
            "/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_chat_agent_service_error(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        mock_agent_service
    ):
        """Test handling of agent service errors."""
        user = test_user
        headers = auth_headers

        # Mock agent service to raise exception
        mock_agent_service.query.side_effect = Exception("Agent service error")

        # Override the agent service dependency
        from main import app
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            response = await client.post(
                "/chat",
                json={"message": "Hello"},
                headers=headers
            )
        finally:
            # Clean up dependency override
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error occurred while processing" in response.json()["detail"].lower()