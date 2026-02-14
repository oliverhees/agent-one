"""ReflexionLog model for agent learning from action outcomes."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ReflexionOutcome(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SUCCESS = "success"


class ReflexionLog(BaseModel):
    __tablename__ = "reflexion_logs"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[ReflexionOutcome] = mapped_column(nullable=False)
    lesson: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="reflexion_logs")
