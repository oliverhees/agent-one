"""N8nWorkflow model for registered n8n workflows."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class N8nWorkflow(BaseModel):
    """Registered n8n workflow callable as external tool."""

    __tablename__ = "n8n_workflows"
    __table_args__ = (
        Index("ix_n8n_workflows_user_active", "user_id", "is_active"),
        {"comment": "Registered n8n workflows as external tools"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this workflow",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Workflow display name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Workflow description",
    )

    webhook_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="n8n webhook trigger URL",
    )

    input_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Expected input parameters schema",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether workflow is active",
    )

    execution_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total execution count",
    )

    last_executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Last execution timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="n8n_workflows",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<N8nWorkflow(id={self.id}, name={self.name})>"
