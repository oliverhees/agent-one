"""Chat service for managing conversations and messages."""

from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select, func, desc, or_, and_, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationNotFoundError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services.ai import AIService


class ChatService:
    """Service for chat operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize chat service.

        Args:
            db: Database session
        """
        self.db = db
        self.ai_service = AIService()

    async def create_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID who owns the conversation
            title: Optional conversation title

        Returns:
            Conversation: Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)

        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        """
        Get a conversation by ID, verifying user ownership.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            Conversation: The conversation

        Raises:
            ConversationNotFoundError: If conversation not found or doesn't belong to user
        """
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ConversationNotFoundError(conversation_id=str(conversation_id))

        return conversation

    async def get_conversations(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[Conversation], UUID | None, bool, int]:
        """
        Get paginated conversations for a user.

        Args:
            user_id: User ID
            cursor: Cursor for pagination (last conversation ID from previous page)
            limit: Maximum number of conversations to return

        Returns:
            tuple: (conversations, next_cursor, has_more, total_count)
        """
        # Build base query with stable sort (updated_at DESC, id DESC)
        query = select(Conversation).where(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at), desc(Conversation.id))

        # Apply cursor pagination if cursor is provided
        if cursor:
            cursor_result = await self.db.execute(
                select(Conversation.updated_at, Conversation.id).where(
                    Conversation.id == cursor
                )
            )
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_updated_at, cursor_id = cursor_row
                # Use composite cursor: items after cursor in (updated_at DESC, id DESC) order
                query = query.where(
                    or_(
                        Conversation.updated_at < cursor_updated_at,
                        and_(
                            Conversation.updated_at == cursor_updated_at,
                            Conversation.id < cursor_id,
                        ),
                    )
                )

        # Fetch one more than limit to check if there are more pages
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        # Determine if there are more pages
        has_more = len(conversations) > limit
        if has_more:
            conversations = conversations[:limit]

        # Get next cursor
        next_cursor = conversations[-1].id if conversations and has_more else None

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(Conversation).where(
                Conversation.user_id == user_id
            )
        )
        total_count = count_result.scalar_one()

        return conversations, next_cursor, has_more, total_count

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], UUID | None, bool]:
        """
        Get paginated messages for a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify conversation ownership
            cursor: Cursor for pagination (last message ID from previous page)
            limit: Maximum number of messages to return

        Returns:
            tuple: (messages, next_cursor, has_more)

        Raises:
            ConversationNotFoundError: If conversation not found or doesn't belong to user
        """
        # Verify conversation ownership
        await self.get_conversation(conversation_id, user_id)

        # Build base query (chronological order)
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())

        # Apply cursor pagination if cursor is provided
        if cursor:
            # Get the cursor message's created_at
            cursor_result = await self.db.execute(
                select(Message.created_at).where(Message.id == cursor)
            )
            cursor_created_at = cursor_result.scalar_one_or_none()

            if cursor_created_at:
                query = query.where(Message.created_at > cursor_created_at)

        # Fetch one more than limit to check if there are more pages
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Determine if there are more pages
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Get next cursor
        next_cursor = messages[-1].id if messages and has_more else None

        return messages, next_cursor, has_more

    async def save_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """
        Save a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dict

        Returns:
            Message: Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        return message

    async def stream_ai_response(
        self,
        conversation_id: UUID,
        user_message: str,
        user_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response for a user message.

        Args:
            conversation_id: Conversation ID
            user_message: User's message content
            user_id: User ID

        Yields:
            str: Streamed text chunks

        Note:
            This is a simplified version. In production, this would:
            - Build context from conversation history
            - Use CrewAI orchestrator
            - Extract mentioned items
            - Store metadata about model, tokens, etc.
        """
        # Get conversation history for context
        messages, _, _ = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=10,  # Last 10 messages for context
        )

        # Build messages array for Claude API
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role.value if msg.role != MessageRole.SYSTEM else "user",
                "content": msg.content,
            })

        # Add current user message
        api_messages.append({
            "role": "user",
            "content": user_message,
        })

        # Stream response from AI service
        async for chunk in self.ai_service.stream_response(
            messages=api_messages,
            system_prompt="You are ALICE, a helpful AI assistant specialized in supporting people with ADHD.",
        ):
            yield chunk
