"""Chat endpoints for messaging and conversation management."""

import json
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import chat_rate_limit, standard_rate_limit
from app.models.message import MessageRole
from app.models.user import User
from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
)
from app.services.chat import ChatService


router = APIRouter(tags=["Chat"])


@router.post(
    "/message",
    status_code=status.HTTP_200_OK,
    summary="Send message (SSE streaming)",
    description="Send a message and receive AI response via Server-Sent Events (SSE).",
    dependencies=[Depends(chat_rate_limit)],
)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and stream AI response.

    - **content**: Message content (1-10000 characters)
    - **conversation_id**: Optional conversation ID (creates new if not provided)

    Returns a Server-Sent Events (SSE) stream with the following event types:
    - **conversation**: Conversation info (first event)
    - **token**: Individual token from AI response
    - **done**: Stream completed with metadata

    Example SSE events:
    ```
    event: conversation
    data: {"conversation_id": "uuid", "is_new": false}

    event: token
    data: {"content": "Hello", "index": 0}

    event: done
    data: {"message_id": "uuid", "total_tokens": 150}
    ```
    """
    chat_service = ChatService(db)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for chat streaming."""
        try:
            # Create or get conversation
            conversation = None
            is_new = False

            if data.conversation_id:
                # Get existing conversation
                conversation = await chat_service.get_conversation(
                    conversation_id=data.conversation_id,
                    user_id=current_user.id,
                )
            else:
                # Create new conversation
                conversation = await chat_service.create_conversation(
                    user_id=current_user.id,
                    title=None,  # Will be auto-generated later
                )
                is_new = True

            # Send conversation info event
            conversation_data = {
                "conversation_id": str(conversation.id),
                "is_new": is_new,
            }
            yield f"event: conversation\n"
            yield f"data: {json.dumps(conversation_data)}\n\n"

            # Save user message
            user_message = await chat_service.save_message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=data.content,
            )

            # Commit the user message
            await db.commit()

            # Stream AI response
            full_response = ""
            token_index = 0

            async for token in chat_service.stream_ai_response(
                conversation_id=conversation.id,
                user_message=data.content,
                user_id=current_user.id,
            ):
                full_response += token
                token_data = {
                    "content": token,
                    "index": token_index,
                }
                yield f"event: token\n"
                yield f"data: {json.dumps(token_data)}\n\n"
                token_index += 1

            # Save assistant message
            assistant_message = await chat_service.save_message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                metadata={
                    "model": "claude-3-5-sonnet-20241022",
                    "total_tokens": len(full_response.split()),  # Simplified
                },
            )

            # Commit assistant message
            await db.commit()

            # Send done event
            done_data = {
                "message_id": str(assistant_message.id),
                "conversation_id": str(conversation.id),
                "total_tokens": len(full_response.split()),
            }
            yield f"event: done\n"
            yield f"data: {json.dumps(done_data)}\n\n"

        except Exception as e:
            # Send error event
            error_data = {
                "detail": str(e),
                "code": "STREAM_ERROR",
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="Get paginated list of user's conversations.",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_conversations(
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of conversations.

    - **cursor**: Optional cursor for pagination (UUID of last item from previous page)
    - **limit**: Number of conversations per page (1-100, default 20)

    Returns conversations sorted by last activity (newest first).
    """
    chat_service = ChatService(db)

    conversations, next_cursor, has_more, total_count = await chat_service.get_conversations(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
    )

    # Convert to response schema
    conversation_responses = [
        ConversationResponse.model_validate(conv)
        for conv in conversations
    ]

    return ConversationListResponse(
        conversations=conversation_responses,
        total=total_count,
        page=1,  # Simplified - cursor-based pagination doesn't have page numbers
        page_size=limit,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get conversation messages",
    description="Get paginated messages for a conversation.",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_conversation_messages(
    conversation_id: UUID,
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get messages for a specific conversation.

    - **conversation_id**: Conversation UUID
    - **cursor**: Optional cursor for pagination (UUID of last message from previous page)
    - **limit**: Number of messages per page (1-100, default 50)

    Returns messages in chronological order (oldest first).
    """
    chat_service = ChatService(db)

    messages, next_cursor, has_more = await chat_service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
    )

    # Convert to response schema
    return [MessageResponse.model_validate(msg) for msg in messages]
