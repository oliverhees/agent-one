"""CalendarEvent model for cached calendar data."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class CalendarEvent(BaseModel):
    """Cached calendar event from external provider."""

    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("ix_calendar_events_user_start", "user_id", "start_time"),
        Index("ix_calendar_events_external", "user_id", "external_id", unique=True),
        {"comment": "Cached calendar events from external providers"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this event",
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="External event ID (e.g. Google Event ID)",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Event title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Event description",
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Event start time (UTC)",
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Event end time (UTC)",
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Event location",
    )

    is_all_day: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is an all-day event",
    )

    calendar_provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="google",
        comment="Calendar provider: google",
    )

    raw_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Original event data from provider",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="calendar_events",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, title={self.title})>"
