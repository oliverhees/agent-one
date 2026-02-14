"""Intervention model."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class InterventionType(str, enum.Enum):
    """Intervention type enum."""

    HYPERFOCUS = "hyperfocus"
    PROCRASTINATION = "procrastination"
    DECISION_FATIGUE = "decision_fatigue"
    TRANSITION = "transition"
    ENERGY_CRASH = "energy_crash"
    SLEEP_DISRUPTION = "sleep_disruption"
    SOCIAL_MASKING = "social_masking"


class InterventionStatus(str, enum.Enum):
    """Intervention status enum."""

    PENDING = "pending"
    DISMISSED = "dismissed"
    ACTED = "acted"


class Intervention(BaseModel):
    """Intervention model representing a proactive wellbeing intervention."""

    __tablename__ = "interventions"
    __table_args__ = (
        Index("ix_interventions_user_status", "user_id", "status"),
        Index("ix_interventions_user_created", "user_id", "created_at"),
        {"comment": "Proactive wellbeing interventions for users"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who receives this intervention",
    )

    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Type: hyperfocus, procrastination, decision_fatigue, transition, energy_crash, sleep_disruption, social_masking",
    )

    trigger_pattern: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Pattern that triggered this intervention",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Intervention message to show to the user",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Status: pending, dismissed, acted",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="interventions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the intervention."""
        return f"<Intervention(id={self.id}, type={self.type}, status={self.status})>"
