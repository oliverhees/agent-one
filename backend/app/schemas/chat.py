"""Chat schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content text",
        examples=["Hallo ALICE, wie geht es dir?"],
    )

    conversation_id: UUID | None = Field(
        None,
        description="Conversation ID (optional, creates new conversation if not provided)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class MessageResponse(BaseModel):
    """Schema for message response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
                "role": "user",
                "content": "Hallo ALICE, wie geht es dir?",
                "created_at": "2026-02-06T10:30:00Z",
            }
        },
    )

    id: UUID = Field(..., description="Message unique identifier")
    conversation_id: UUID = Field(..., description="Conversation ID this message belongs to")
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content text")
    created_at: datetime = Field(..., description="Message creation timestamp")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Chat über ADHS Strategien",
                "created_at": "2026-02-06T10:30:00Z",
                "updated_at": "2026-02-06T11:45:00Z",
            }
        },
    )

    id: UUID = Field(..., description="Conversation unique identifier")
    user_id: UUID = Field(..., description="User who owns this conversation")
    title: str | None = Field(None, description="Conversation title")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    updated_at: datetime = Field(..., description="Last activity timestamp")


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list response."""

    conversations: list[ConversationResponse] = Field(
        ...,
        description="List of conversations",
    )

    total: int = Field(
        ...,
        description="Total number of conversations",
        examples=[42],
    )

    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        examples=[1],
    )

    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page",
        examples=[20],
    )
