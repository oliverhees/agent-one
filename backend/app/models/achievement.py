"""Achievement and UserAchievement models."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AchievementCategory(str, enum.Enum):
    """Achievement category enum."""

    TASK = "task"
    STREAK = "streak"
    BRAIN = "brain"
    SOCIAL = "social"
    SPECIAL = "special"


class Achievement(BaseModel):
    """Achievement definition for gamification."""

    __tablename__ = "achievements"
    __table_args__ = {"comment": "Achievement definitions for gamification"}

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Achievement name (unique)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Achievement description",
    )

    icon: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Emoji or icon name",
    )

    category: Mapped[AchievementCategory] = mapped_column(
        SQLEnum(
            AchievementCategory,
            name="achievement_category",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        index=True,
        comment="Category: task, streak, brain, social, special",
    )

    condition_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Condition type, e.g. tasks_completed, streak_days, brain_entries",
    )

    condition_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Condition threshold value",
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="XP reward when unlocked",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Is this achievement active?",
    )

    # Relationships
    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="achievement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Achievement(id={self.id}, name={self.name!r}, category={self.category.value})>"


class UserAchievement(BaseModel):
    """Tracks unlocked achievements per user."""

    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievements_user_achievement"),
        {"comment": "Unlocked achievements per user"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who unlocked this achievement",
    )

    achievement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Achievement that was unlocked",
    )

    unlocked_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        comment="When the achievement was unlocked",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="user_achievements",
        lazy="selectin",
    )

    achievement: Mapped["Achievement"] = relationship(
        back_populates="user_achievements",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"
