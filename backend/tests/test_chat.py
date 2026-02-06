"""Chat endpoint tests."""

import json
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat import ChatService
from app.models.message import MessageRole


class TestSendMessage:
    """Tests for /api/v1/chat/message endpoint (SSE streaming)."""

    async def test_send_message_creates_conversation(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
    ):
        """Test sending a message creates a new conversation."""
        response = await authenticated_client.post(
            "/api/v1/chat/message",
            json={"content": "Hello ALICE, how are you?"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE stream
        events = []
        for line in response.text.split("\n\n"):
            if line.strip():
                event_type = None
                event_data = None
                for part in line.split("\n"):
                    if part.startswith("event: "):
                        event_type = part[7:]
                    elif part.startswith("data: "):
                        event_data = json.loads(part[6:])
                if event_type and event_data:
                    events.append({"type": event_type, "data": event_data})

        # Check that we got the expected events
        assert len(events) >= 3  # conversation, token(s), done

        # First event should be conversation with is_new=True
        assert events[0]["type"] == "conversation"
        assert events[0]["data"]["is_new"] is True
        assert "conversation_id" in events[0]["data"]

        # Should have token events
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) > 0

        # Last event should be done
        assert events[-1]["type"] == "done"
        assert "message_id" in events[-1]["data"]
        assert "conversation_id" in events[-1]["data"]

    async def test_send_message_existing_conversation(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_db: AsyncSession,
    ):
        """Test sending a message to an existing conversation."""
        user_dict, _, _ = test_user

        # Create a conversation first
        chat_service = ChatService(test_db)
        conversation = await chat_service.create_conversation(
            user_id=user_dict["id"],
            title="Test Conversation",
        )
        await test_db.commit()

        response = await authenticated_client.post(
            "/api/v1/chat/message",
            json={
                "content": "This is a follow-up message",
                "conversation_id": str(conversation.id),
            },
        )

        assert response.status_code == 200

        # Parse SSE stream
        events = []
        for line in response.text.split("\n\n"):
            if line.strip():
                event_type = None
                event_data = None
                for part in line.split("\n"):
                    if part.startswith("event: "):
                        event_type = part[7:]
                    elif part.startswith("data: "):
                        event_data = json.loads(part[6:])
                if event_type and event_data:
                    events.append({"type": event_type, "data": event_data})

        # First event should be conversation with is_new=False
        assert events[0]["type"] == "conversation"
        assert events[0]["data"]["is_new"] is False
        assert events[0]["data"]["conversation_id"] == str(conversation.id)

    async def test_send_message_unauthenticated(self, client: AsyncClient):
        """Test sending message without authentication."""
        response = await client.post(
            "/api/v1/chat/message",
            json={"content": "Hello"},
        )

        assert response.status_code == 403  # HTTPBearer returns 403


class TestListConversations:
    """Tests for /api/v1/chat/conversations endpoint."""

    async def test_get_conversations_empty(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting conversations when user has none."""
        response = await authenticated_client.get("/api/v1/chat/conversations")

        assert response.status_code == 200
        data = response.json()

        assert "conversations" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        assert data["conversations"] == []
        assert data["total"] == 0

    async def test_get_conversations_with_data(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_db: AsyncSession,
    ):
        """Test getting conversations when user has some."""
        user_dict, _, _ = test_user
        chat_service = ChatService(test_db)

        # Create 3 conversations
        for i in range(3):
            conv = await chat_service.create_conversation(
                user_id=user_dict["id"],
                title=f"Conversation {i+1}",
            )
            # Add a message to each
            await chat_service.save_message(
                conversation_id=conv.id,
                role=MessageRole.USER,
                content=f"Message {i+1}",
            )

        await test_db.commit()

        response = await authenticated_client.get("/api/v1/chat/conversations")

        assert response.status_code == 200
        data = response.json()

        assert len(data["conversations"]) == 3
        assert data["total"] == 3
        assert data["page_size"] == 20

        # Check conversation structure
        conv = data["conversations"][0]
        assert "id" in conv
        assert "user_id" in conv
        assert "title" in conv
        assert "created_at" in conv
        assert "updated_at" in conv

    async def test_get_conversations_pagination(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_db: AsyncSession,
    ):
        """Test conversation pagination with cursor."""
        user_dict, _, _ = test_user
        chat_service = ChatService(test_db)

        # Create 25 conversations
        for i in range(25):
            await chat_service.create_conversation(
                user_id=user_dict["id"],
                title=f"Conversation {i+1}",
            )

        await test_db.commit()

        # Get first page (limit 20)
        response1 = await authenticated_client.get(
            "/api/v1/chat/conversations?limit=20"
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["conversations"]) == 20
        assert data1["total"] == 25

        # Get second page using cursor
        last_id = data1["conversations"][-1]["id"]
        response2 = await authenticated_client.get(
            f"/api/v1/chat/conversations?cursor={last_id}&limit=20"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["conversations"]) == 5

    async def test_get_conversations_unauthenticated(self, client: AsyncClient):
        """Test getting conversations without authentication."""
        response = await client.get("/api/v1/chat/conversations")

        assert response.status_code == 403  # HTTPBearer returns 403


class TestGetMessages:
    """Tests for /api/v1/chat/conversations/{conversation_id}/messages endpoint."""

    async def test_get_messages_success(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_db: AsyncSession,
    ):
        """Test getting messages for a conversation."""
        user_dict, _, _ = test_user
        chat_service = ChatService(test_db)

        # Create conversation with messages
        conv = await chat_service.create_conversation(
            user_id=user_dict["id"],
            title="Test Chat",
        )

        await chat_service.save_message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Hello",
        )

        await chat_service.save_message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="Hi there!",
        )

        await test_db.commit()

        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{conv.id}/messages"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        # Check message structure
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Hello"
        assert data[1]["role"] == "assistant"
        assert data[1]["content"] == "Hi there!"

        # Check fields
        for msg in data:
            assert "id" in msg
            assert "conversation_id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "created_at" in msg

    async def test_get_messages_wrong_conversation(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
        second_user: tuple[dict, str, str],
        test_db: AsyncSession,
    ):
        """Test getting messages from another user's conversation."""
        second_user_dict, _, _ = second_user
        chat_service = ChatService(test_db)

        # Create conversation for second user
        conv = await chat_service.create_conversation(
            user_id=second_user_dict["id"],
            title="Private Conversation",
        )
        await test_db.commit()

        # Try to access with first user's auth
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{conv.id}/messages"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_get_messages_nonexistent_conversation(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting messages for a conversation that doesn't exist."""
        fake_id = uuid4()
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{fake_id}/messages"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_get_messages_unauthenticated(
        self,
        client: AsyncClient,
    ):
        """Test getting messages without authentication."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/chat/conversations/{fake_id}/messages"
        )

        assert response.status_code == 403  # HTTPBearer returns 403
