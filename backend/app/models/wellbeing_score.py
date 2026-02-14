"""WellbeingScore model."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class WellbeingZone(str, enum.Enum):
    """Wellbeing zone enum."""

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class WellbeingScore(BaseModel):
    """WellbeingScore model representing a user's wellbeing assessment."""

    __tablename__ = "wellbeing_scores"
    __table_args__ = (
        Index("ix_wellbeing_scores_user_created", "user_id", "created_at"),
        {"comment": "User wellbeing scores with zone classification"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this wellbeing score",
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Overall wellbeing score (0.0 to 1.0)",
    )

    zone: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Wellbeing zone: red, yellow, green",
    )

    components: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Component scores (energy, focus, stress, etc.)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="wellbeing_scores",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the wellbeing score."""
        return f"<WellbeingScore(id={self.id}, score={self.score}, zone={self.zone})>"
