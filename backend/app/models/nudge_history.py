"""NudgeHistory model."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class NudgeType(str, enum.Enum):
    """Nudge type enum."""

    FOLLOW_UP = "follow_up"
    DEADLINE = "deadline"
    STREAK_REMINDER = "streak_reminder"
    MOTIVATIONAL = "motivational"


class NudgeHistory(BaseModel):
    """Nudge/reminder history for ADHS mode."""

    __tablename__ = "nudge_history"
    __table_args__ = {"comment": "Nudge/reminder history for ADHS mode"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who received this nudge",
    )

    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        comment="Related task (if applicable)",
    )

    nudge_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Nudge intensity: 1=friendly, 2=firm, 3=urgent",
    )

    nudge_type: Mapped[NudgeType] = mapped_column(
        SQLEnum(
            NudgeType,
            name="nudge_type",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        comment="Type: follow_up, deadline, streak_reminder, motivational",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Nudge message text",
    )

    delivered_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        comment="When the nudge was delivered",
    )

    acknowledged_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the user acknowledged the nudge",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="nudges",
        lazy="selectin",
    )

    task: Mapped["Task | None"] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<NudgeHistory(id={self.id}, user_id={self.user_id}, type={self.nudge_type.value})>"
