"""PredictedPattern model for behavioral pattern predictions."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class PredictionStatus(str, enum.Enum):
    """Status of a prediction."""

    ACTIVE = "active"
    CONFIRMED = "confirmed"
    AVOIDED = "avoided"
    EXPIRED = "expired"


class PredictedPattern(BaseModel):
    """Predicted behavioral pattern for a user."""

    __tablename__ = "predicted_patterns"
    __table_args__ = (
        Index("ix_predicted_patterns_user_status", "user_id", "status"),
        Index("ix_predicted_patterns_user_predicted", "user_id", "predicted_for"),
        {"comment": "ADHS behavioral pattern predictions"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this prediction belongs to",
    )

    pattern_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="One of 7 InterventionType values",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence score 0.0-1.0",
    )

    predicted_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the pattern is predicted to occur",
    )

    time_horizon: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Prediction horizon: 24h, 3d, 7d",
    )

    trigger_factors: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Metrics that triggered this prediction",
    )

    graphiti_context: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Optional enrichment from knowledge graph",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PredictionStatus.ACTIVE,
        comment="Status: active, confirmed, avoided, expired",
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When the prediction was resolved",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="predicted_patterns",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PredictedPattern(id={self.id}, type={self.pattern_type}, "
            f"confidence={self.confidence}, status={self.status})>"
        )
