"""Personality template model for predefined personality presets."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.personality_profile import PersonalityProfile


class PersonalityTemplate(Base):
    """Personality template model for predefined personality presets.

    Note: This model only has created_at (no updated_at) as per SCHEMA.md.
    Templates are seed data and rarely modified.
    """

    __tablename__ = "personality_templates"
    __table_args__ = (
        {"comment": "Predefined personality templates as starting points"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Template name",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template description",
    )

    traits: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Predefined trait values (formality, humor, strictness, empathy, verbosity)",
    )

    rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Predefined rules",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Is this the default template for new users?",
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Icon identifier (e.g. shield, heart)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    profiles: Mapped[list["PersonalityProfile"]] = relationship(
        back_populates="template",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the personality template."""
        return f"<PersonalityTemplate(id={self.id}, name={self.name!r})>"
