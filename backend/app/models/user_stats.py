"""UserStats model."""

import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class UserStats(BaseModel):
    """Gamification stats per user (1:1 with users)."""

    __tablename__ = "user_stats"
    __table_args__ = {"comment": "Gamification stats per user (1:1 with users)"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User who owns these stats",
    )

    total_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Total XP earned",
    )

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Current level",
    )

    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Current streak in consecutive active days",
    )

    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Longest streak ever achieved",
    )

    last_active_date: Mapped[Any | None] = mapped_column(
        Date,
        nullable=True,
        comment="Last date with a completed task",
    )

    tasks_completed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Total number of completed tasks",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="user_stats",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserStats(user_id={self.user_id}, level={self.level}, xp={self.total_xp})>"
