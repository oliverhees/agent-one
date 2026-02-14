"""Webhook models for incoming/outgoing integrations."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class WebhookDirection(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class WebhookConfig(BaseModel):
    """Webhook configuration for incoming/outgoing integrations."""

    __tablename__ = "webhook_configs"
    __table_args__ = (
        Index("ix_webhook_configs_user_active", "user_id", "is_active"),
        {"comment": "Webhook configurations for external integrations"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this webhook",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Webhook display name",
    )

    url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="Target URL for outgoing / display URL for incoming",
    )

    secret: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="HMAC secret (encrypted via Fernet)",
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Direction: incoming or outgoing",
    )

    events: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="List of event types (outgoing only)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether webhook is active",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="webhook_configs",
        lazy="selectin",
    )

    logs: Mapped[list["WebhookLog"]] = relationship(
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig(id={self.id}, name={self.name}, dir={self.direction})>"


class WebhookLog(BaseModel):
    """Log entry for webhook executions."""

    __tablename__ = "webhook_logs"
    __table_args__ = (
        Index("ix_webhook_logs_webhook_created", "webhook_id", "created_at"),
        {"comment": "Webhook execution logs"},
    )

    webhook_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Webhook this log belongs to",
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Direction: incoming or outgoing",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Event type that triggered this log",
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Request payload",
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP response status code",
    )

    response_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Response body (truncated to 1000 chars)",
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Attempt number (1-3)",
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether the webhook call succeeded",
    )

    # Relationships
    webhook: Mapped["WebhookConfig"] = relationship(
        back_populates="logs",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WebhookLog(id={self.id}, event={self.event_type}, success={self.success})>"
