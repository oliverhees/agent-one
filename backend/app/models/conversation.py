"""Conversation model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class Conversation(BaseModel):
    """Conversation model representing a chat conversation."""

    __tablename__ = "conversations"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this conversation",
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Conversation title (auto-generated or manual)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="conversations",
        lazy="selectin",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the conversation."""
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title})>"
