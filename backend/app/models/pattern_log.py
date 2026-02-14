"""PatternLog model for NLP conversation analysis scores."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User


class PatternLog(BaseModel):
    """Stores NLP analysis scores per conversation for trend tracking."""

    __tablename__ = "pattern_logs"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this analysis belongs to",
    )

    conversation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Conversation that was analyzed",
    )

    episode_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Graphiti episode reference ID",
    )

    mood_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Mood: -1.0 (negative) to 1.0 (positive)",
    )

    energy_level: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Energy: 0.0 (low) to 1.0 (high)",
    )

    focus_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Focus: 0.0 (unfocused) to 1.0 (focused)",
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")

    conversation: Mapped["Conversation | None"] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the pattern log."""
        return (
            f"<PatternLog(id={self.id}, user_id={self.user_id}, "
            f"mood={self.mood_score}, energy={self.energy_level}, focus={self.focus_score})>"
        )
