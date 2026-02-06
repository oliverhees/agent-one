"""Message model."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class MessageRole(str, enum.Enum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model representing a single message in a conversation."""

    __tablename__ = "messages"

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Conversation this message belongs to",
    )

    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, name="message_role", create_type=True),
        nullable=False,
        comment="Message role: user, assistant, or system",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message content text",
    )

    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional message metadata (model info, tokens, etc.)",
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the message."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role.value}, content={content_preview!r})>"
