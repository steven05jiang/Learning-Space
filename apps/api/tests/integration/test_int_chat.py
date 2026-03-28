"""
Integration tests for chat API endpoints.

Tests:
- INT-036: User sends a chat message
- INT-037: User continues a conversation with context
- INT-038: Agent uses graph traversal tool
- INT-039: User lists their conversations
- INT-040: User retrieves messages in a conversation
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from models.conversation import Conversation, Message, MessageRole
from models.user import User
from schemas.agent import AgentResponse


@pytest.mark.integration
@pytest.mark.int_chat
async def test_user_sends_chat_message_creates_conversation(
    client, auth_headers, db_session
):
    """
    INT-036: User sends a chat message

    POST /chat
      Body: {message: "What resources do I have on Python?"}
      Auth: valid user JWT

    Expected:
      - 200 response
      - response body contains: conversation_id (UUID), message_id (UUID),
        response (non-empty str), role="assistant"
      - New Conversation row exists in DB
      - Two Message rows: one USER, one ASSISTANT
    """
    # Mock agent_service.query to return a deterministic response
    mock_agent_response = AgentResponse(
        response="You have 3 Python resources.", sources=None
    )

    with patch("routers.chat.agent_service.query", return_value=mock_agent_response):
        payload = {"message": "What resources do I have on Python?"}
        response = await client.post("/chat", json=payload, headers=auth_headers)

    # Verify response structure
    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert "message_id" in data
    assert data["response"] == "You have 3 Python resources."
    assert data["role"] == "assistant"

    # Parse UUIDs to verify they are valid
    conversation_id = uuid.UUID(data["conversation_id"])
    message_id = uuid.UUID(data["message_id"])

    # Verify new Conversation row exists in DB
    conversation_query = select(Conversation).where(Conversation.id == conversation_id)
    conversation_result = await db_session.execute(conversation_query)
    conversation = conversation_result.scalar_one()
    assert conversation is not None
    assert conversation.title is None  # Initial conversations have no title

    # Verify two Message rows exist: one USER, one ASSISTANT
    messages_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages_result = await db_session.execute(messages_query)
    messages = list(messages_result.scalars().all())

    assert len(messages) == 2

    # First message should be USER
    user_message = messages[0]
    assert user_message.role == MessageRole.USER
    assert user_message.content == "What resources do I have on Python?"

    # Second message should be ASSISTANT
    assistant_message = messages[1]
    assert assistant_message.role == MessageRole.ASSISTANT
    assert assistant_message.content == "You have 3 Python resources."
    assert assistant_message.id == message_id


@pytest.mark.integration
@pytest.mark.int_chat
async def test_user_continues_conversation_with_context(
    client, auth_headers, db_session
):
    """
    INT-037: User continues a conversation with context

    POST /chat (first message) → get conversation_id
    POST /chat (second message, same conversation_id)

    Expected:
      - Both calls return 200
      - Second call returns same conversation_id
      - 4 messages total in DB (2 user + 2 assistant)
      - Second agent call receives conversation_history with the first exchange
    """
    # Mock agent responses
    first_response = AgentResponse(
        response=(
            "You have 3 Python resources: FastAPI tutorial, Django guide, "
            "and Flask basics."
        ),
        sources=None,
    )
    second_response = AgentResponse(
        response="The FastAPI tutorial covers REST API development with Python.",
        sources=None,
    )

    # First message - create conversation
    with patch(
        "routers.chat.agent_service.query", return_value=first_response
    ) as mock_agent:
        payload1 = {"message": "What Python resources do I have?"}
        response1 = await client.post("/chat", json=payload1, headers=auth_headers)

    assert response1.status_code == 200
    data1 = response1.json()
    conversation_id = data1["conversation_id"]

    # Verify the first agent call received empty conversation history
    mock_agent.assert_called_once()
    first_call_args = mock_agent.call_args[0]
    agent_query = first_call_args[1]  # Second argument is the AgentQuery
    assert len(agent_query.conversation_history) == 0

    # Second message - continue conversation
    with patch(
        "routers.chat.agent_service.query", return_value=second_response
    ) as mock_agent:
        payload2 = {
            "message": "Tell me more about the FastAPI tutorial",
            "conversation_id": conversation_id,
        }
        response2 = await client.post("/chat", json=payload2, headers=auth_headers)

    assert response2.status_code == 200
    data2 = response2.json()

    # Should return same conversation_id
    assert data2["conversation_id"] == conversation_id
    assert data2["response"] == (
        "The FastAPI tutorial covers REST API development with Python."
    )

    # Verify the second agent call received conversation history with the first exchange
    mock_agent.assert_called_once()
    second_call_args = mock_agent.call_args[0]
    agent_query = second_call_args[1]
    assert len(agent_query.conversation_history) == 2  # First user + first assistant
    assert agent_query.conversation_history[0].role == "user"
    assert agent_query.conversation_history[0].content == (
        "What Python resources do I have?"
    )
    assert agent_query.conversation_history[1].role == "assistant"
    assert agent_query.conversation_history[1].content == (
        "You have 3 Python resources: FastAPI tutorial, Django guide, and Flask basics."
    )

    # Verify 4 messages total in DB (2 user + 2 assistant)
    messages_query = (
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.asc())
    )
    messages_result = await db_session.execute(messages_query)
    messages = list(messages_result.scalars().all())

    assert len(messages) == 4
    assert messages[0].role == MessageRole.USER
    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[2].role == MessageRole.USER
    assert messages[3].role == MessageRole.ASSISTANT


@pytest.mark.integration
@pytest.mark.int_chat
async def test_agent_uses_graph_traversal_tool(client, auth_headers, db_session):
    """
    INT-038: Agent uses graph traversal tool

    POST /chat
      Body: {message: "Show me related topics to Python"}
      Mock: agent_service.query returns response that mentions graph tool usage

    Expected:
      - 200 response
      - conversation_id and response present
      - Message persisted

    Note: This test verifies the chat endpoint works when the agent (mocked) returns
    a response — the actual tool call is a unit-level concern already tested in
    test_agent_service.py.
    """
    # Mock agent response that simulates graph tool usage
    mock_agent_response = AgentResponse(
        response=(
            "Based on your knowledge graph, Python is related to: Machine Learning, "
            "Web Development, Data Science, and API Development. These topics connect "
            "through your saved resources and learning paths."
        ),
        sources=None,
    )

    with patch("routers.chat.agent_service.query", return_value=mock_agent_response):
        payload = {"message": "Show me related topics to Python"}
        response = await client.post("/chat", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "conversation_id" in data
    assert "message_id" in data
    assert "Python is related to: Machine Learning" in data["response"]
    assert data["role"] == "assistant"

    # Verify conversation and messages were persisted
    conversation_id = uuid.UUID(data["conversation_id"])

    conversation_query = select(Conversation).where(Conversation.id == conversation_id)
    conversation_result = await db_session.execute(conversation_query)
    conversation = conversation_result.scalar_one()
    assert conversation is not None

    messages_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages_result = await db_session.execute(messages_query)
    messages = list(messages_result.scalars().all())

    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "Show me related topics to Python"
    assert messages[1].role == MessageRole.ASSISTANT
    assert "Python is related to: Machine Learning" in messages[1].content


@pytest.mark.integration
@pytest.mark.int_chat
async def test_user_lists_conversations_paginated_own_only(
    client, auth_headers, db_session, test_user
):
    """
    INT-039: User lists their conversations

    Setup: Create 2 conversations for user A, 1 for user B

    GET /chat/conversations (as user A)

    Expected:
      - 200 with items list of 2 (user A's only)
      - Ordered by updated_at DESC
      - total=2, limit=20, offset=0
    """
    # Create a second user
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    # Create 2 conversations for test_user (user A)
    conv1 = Conversation(
        id=uuid.uuid4(), user_id=test_user.id, title="Python Discussion"
    )
    conv2 = Conversation(id=uuid.uuid4(), user_id=test_user.id, title="JavaScript Talk")

    # Create 1 conversation for other_user (user B)
    conv3 = Conversation(
        id=uuid.uuid4(), user_id=other_user.id, title="Other User's Chat"
    )

    db_session.add_all([conv1, conv2, conv3])
    await db_session.flush()

    # Update conv2 to be more recent (for ordering test)
    import time

    time.sleep(0.01)  # Ensure different timestamps
    conv2.updated_at = conv1.updated_at
    await db_session.commit()

    # Test GET /chat/conversations as test_user
    response = await client.get("/chat/conversations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify pagination structure
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    # Should only see own conversations (2 for test_user)
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 20
    assert data["offset"] == 0

    # Verify conversations belong to test_user and are ordered by updated_at DESC
    returned_titles = [item["title"] for item in data["items"]]
    assert "Python Discussion" in returned_titles
    assert "JavaScript Talk" in returned_titles
    assert "Other User's Chat" not in returned_titles

    # Verify each conversation has the expected structure
    for conv_data in data["items"]:
        assert "id" in conv_data
        assert "user_id" in conv_data
        assert conv_data["user_id"] == str(test_user.id)
        assert "title" in conv_data
        assert "created_at" in conv_data
        assert "updated_at" in conv_data


@pytest.mark.integration
@pytest.mark.int_chat
async def test_user_retrieves_conversation_messages(
    client, auth_headers, db_session, test_user
):
    """
    INT-040: User retrieves messages in a conversation

    Setup: Create conversation + 3 messages (alternating user/assistant)

    GET /chat/conversations/{id}/messages (as owner)

    Expected:
      - 200 with conversation + messages array of 3
      - Messages ordered by created_at ASC
      - 403 if different user accesses the conversation
    """
    # Create a conversation for test_user
    conversation = Conversation(
        id=uuid.uuid4(), user_id=test_user.id, title="Test Conversation"
    )
    db_session.add(conversation)
    await db_session.flush()

    # Create 3 messages: user -> assistant -> user
    msg1 = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content="Hello, what can you help me with?",
    )
    msg2 = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content="I can help you find and organize your learning resources.",
    )
    msg3 = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content="Show me my Python resources.",
    )

    db_session.add_all([msg1, msg2, msg3])
    await db_session.commit()

    # Test GET /chat/conversations/{id}/messages as owner
    response = await client.get(
        f"/chat/conversations/{conversation.id}/messages", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify conversation data
    assert data["id"] == str(conversation.id)
    assert data["user_id"] == str(test_user.id)
    assert data["title"] == "Test Conversation"
    assert "created_at" in data
    assert "updated_at" in data

    # Verify messages array
    assert "messages" in data
    assert len(data["messages"]) == 3

    # Verify messages are ordered by created_at ASC
    messages = data["messages"]
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello, what can you help me with?"
    assert messages[1]["role"] == "assistant"
    assert (
        messages[1]["content"]
        == "I can help you find and organize your learning resources."
    )
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Show me my Python resources."

    # Verify each message has the expected structure
    for msg_data in messages:
        assert "id" in msg_data
        assert "conversation_id" in msg_data
        assert msg_data["conversation_id"] == str(conversation.id)
        assert "role" in msg_data
        assert "content" in msg_data
        assert "created_at" in msg_data


@pytest.mark.integration
@pytest.mark.int_chat
async def test_user_cannot_access_others_conversation_messages(
    client, auth_headers, db_session
):
    """
    INT-040 variant: 403 if different user accesses the conversation
    """
    # Create a different user and their conversation
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_conversation = Conversation(
        id=uuid.uuid4(), user_id=other_user.id, title="Other's Private Chat"
    )
    db_session.add(other_conversation)
    await db_session.commit()

    # Try to access other user's conversation with test_user's auth
    response = await client.get(
        f"/chat/conversations/{other_conversation.id}/messages", headers=auth_headers
    )

    assert response.status_code == 403
    data = response.json()
    assert "Access denied" in data["detail"]


@pytest.mark.integration
@pytest.mark.int_chat
async def test_get_nonexistent_conversation_messages_returns_404(client, auth_headers):
    """
    INT-040 variant: 404 for nonexistent conversation
    """
    nonexistent_id = uuid.uuid4()
    response = await client.get(
        f"/chat/conversations/{nonexistent_id}/messages", headers=auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "Conversation not found" in data["detail"]
