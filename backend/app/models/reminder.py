"""Reminder model for smart reminders."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ReminderSource(str, enum.Enum):
    MANUAL = "manual"
    CHAT = "chat"
    CALENDAR = "calendar"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"


class ReminderRecurrence(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Reminder(BaseModel):
    """Smart reminder with multiple sources and recurrence."""

    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_user_status", "user_id", "status"),
        Index("ix_reminders_user_remind_at", "user_id", "remind_at"),
        {"comment": "Smart reminders from manual, chat, or calendar sources"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this reminder",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Reminder title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reminder description",
    )

    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When to send the reminder (UTC)",
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReminderSource.MANUAL,
        comment="Source: manual, chat, calendar",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReminderStatus.PENDING,
        comment="Status: pending, sent, dismissed, snoozed",
    )

    recurrence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        comment="Recurrence: daily, weekly, monthly, or null",
    )

    recurrence_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="End date for recurring reminders",
    )

    linked_task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional linked task",
    )

    linked_event_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional linked calendar event",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="reminders",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, title={self.title}, status={self.status})>"
