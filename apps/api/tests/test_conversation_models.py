"""Tests for conversation and message models."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from models.conversation import MessageRole as ModelMessageRole
from schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from schemas.conversation import (
    MessageRole as SchemaMessageRole,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_schema_message_role_values(self):
        """Test that Pydantic MessageRole enum has correct values."""
        assert SchemaMessageRole.USER.value == "user"
        assert SchemaMessageRole.ASSISTANT.value == "assistant"

    def test_model_message_role_values(self):
        """Test that SQLAlchemy MessageRole enum has correct values."""
        assert ModelMessageRole.USER.value == "user"
        assert ModelMessageRole.ASSISTANT.value == "assistant"


class TestConversationSchemas:
    """Test conversation Pydantic schemas."""

    def test_conversation_create_valid(self):
        """Test valid conversation creation."""
        data = ConversationCreate(title="Test Conversation")
        assert data.title == "Test Conversation"

    def test_conversation_create_empty_title(self):
        """Test conversation creation with empty title."""
        data = ConversationCreate(title="")
        assert data.title is None

    def test_conversation_create_whitespace_title(self):
        """Test conversation creation with whitespace-only title."""
        data = ConversationCreate(title="   ")
        assert data.title is None

    def test_conversation_create_no_title(self):
        """Test conversation creation without title."""
        data = ConversationCreate()
        assert data.title is None

    def test_conversation_update_valid(self):
        """Test valid conversation update."""
        data = ConversationUpdate(title="Updated Title")
        assert data.title == "Updated Title"

    def test_conversation_update_empty_title(self):
        """Test conversation update with empty title."""
        data = ConversationUpdate(title="")
        assert data.title is None


class TestMessageSchemas:
    """Test message Pydantic schemas."""

    def test_message_create_valid_user(self):
        """Test valid user message creation."""
        data = MessageCreate(role=SchemaMessageRole.USER, content="Hello!")
        assert data.role == SchemaMessageRole.USER
        assert data.content == "Hello!"

    def test_message_create_valid_assistant(self):
        """Test valid assistant message creation."""
        data = MessageCreate(role=SchemaMessageRole.ASSISTANT, content="Hi there!")
        assert data.role == SchemaMessageRole.ASSISTANT
        assert data.content == "Hi there!"

    def test_message_create_strips_content(self):
        """Test that content is stripped of whitespace."""
        data = MessageCreate(role=SchemaMessageRole.USER, content="  Hello!  ")
        assert data.content == "Hello!"

    def test_message_create_empty_content_raises_error(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            MessageCreate(role=SchemaMessageRole.USER, content="")

    def test_message_create_whitespace_content_raises_error(self):
        """Test that whitespace-only content raises validation error."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            MessageCreate(role=SchemaMessageRole.USER, content="   ")


class TestSchemaResponses:
    """Test response schema models."""

    def test_conversation_response_creation(self):
        """Test ConversationResponse can be created."""
        now = datetime.now(UTC)
        test_uuid = uuid4()
        data = ConversationResponse(
            id=test_uuid, user_id=1, title="Test", created_at=now, updated_at=now
        )
        assert data.id == test_uuid
        assert data.user_id == 1
        assert data.title == "Test"
        assert data.created_at == now
        assert data.updated_at == now

    def test_message_response_creation(self):
        """Test MessageResponse can be created."""
        now = datetime.now(UTC)
        message_uuid = uuid4()
        conversation_uuid = uuid4()
        data = MessageResponse(
            id=message_uuid,
            conversation_id=conversation_uuid,
            role=SchemaMessageRole.USER,
            content="Hello!",
            created_at=now,
        )
        assert data.id == message_uuid
        assert data.conversation_id == conversation_uuid
        assert data.role == SchemaMessageRole.USER
        assert data.content == "Hello!"
        assert data.created_at == now
