"""Mentioned item model for proactive chat extraction."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import Base

from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class MentionedItemType(str, enum.Enum):
    """Mentioned item type enum."""

    TASK = "task"
    APPOINTMENT = "appointment"
    IDEA = "idea"
    FOLLOW_UP = "follow_up"
    REMINDER = "reminder"


class MentionedItemStatus(str, enum.Enum):
    """Mentioned item status enum."""

    PENDING = "pending"
    CONVERTED = "converted"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"


class MentionedItem(Base):
    """Mentioned item model for items extracted from chat messages.

    Note: This model only has created_at (no updated_at) as per SCHEMA.md.
    """

    __tablename__ = "mentioned_items"
    __table_args__ = (
        Index("ix_mentioned_items_user_status", "user_id", "status"),
        {"comment": "Items extracted from chat messages (tasks, appointments, ideas, etc.)"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this item",
    )

    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source message this item was extracted from",
    )

    item_type: Mapped[MentionedItemType] = mapped_column(
        SQLEnum(MentionedItemType, name="mentioned_item_type", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        comment="Type: task, appointment, idea, follow_up, reminder",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Extracted content",
    )

    status: Mapped[MentionedItemStatus] = mapped_column(
        SQLEnum(MentionedItemStatus, name="mentioned_item_status", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="pending",
        comment="Status: pending, converted, dismissed, snoozed",
    )

    extracted_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Structured extracted data (suggested_title, priority, etc.)",
    )

    converted_to_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="ID of the created task/brain_entry after conversion",
    )

    converted_to_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of converted entity: task or brain_entry",
    )

    snoozed_until: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Snoozed until timestamp",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="mentioned_items",
        lazy="selectin",
    )

    message: Mapped["Message"] = relationship(
        back_populates="mentioned_items",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the mentioned item."""
        return f"<MentionedItem(id={self.id}, type={self.item_type.value}, status={self.status.value})>"
