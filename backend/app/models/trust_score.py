"""TrustScore model for progressive agent autonomy."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class TrustScore(BaseModel):
    __tablename__ = "trust_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "agent_type", "action_type", name="uq_trust_user_agent_action"),
    )

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="email, calendar, research, briefing")
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="read, write, delete, send")
    trust_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="1=new, 2=trusted, 3=autonomous")
    successful_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_escalation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_violation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="trust_scores")
