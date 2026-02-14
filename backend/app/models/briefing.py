"""Briefing model for daily Morning Briefings."""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class BriefingStatus(str, enum.Enum):
    """Status of a briefing."""

    GENERATED = "generated"
    DELIVERED = "delivered"
    READ = "read"


class Briefing(BaseModel):
    """Daily Morning Briefing for a user."""

    __tablename__ = "briefings"
    __table_args__ = (
        Index("ix_briefings_user_date", "user_id", "briefing_date"),
        Index("ix_briefings_user_status", "user_id", "status"),
        {"comment": "Daily Morning Briefings"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this briefing belongs to",
    )

    briefing_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        comment="Date this briefing is for",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="LLM-generated briefing text (German)",
    )

    tasks_suggested: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Prioritized task list [{task_id, title, priority, reason}]",
    )

    wellbeing_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Wellbeing score snapshot at generation time",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BriefingStatus.GENERATED,
        comment="Briefing lifecycle status: generated, delivered, read",
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When the user opened the briefing",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="briefings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the briefing."""
        return f"<Briefing(id={self.id}, user_id={self.user_id}, date={self.briefing_date}, status={self.status})>"
