"""Personality profile model for customizable ALICE personalities."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.personality_template import PersonalityTemplate
    from app.models.user import User


class PersonalityProfile(BaseModel):
    """Personality profile model representing a user's customized personality for ALICE."""

    __tablename__ = "personality_profiles"
    __table_args__ = (
        Index(
            "ix_personality_profiles_user_active",
            "user_id",
            unique=True,
            postgresql_where="is_active = true",
        ),
        {"comment": "Customizable personality profiles for ALICE"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this profile",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Profile name (e.g. 'Mein Coach')",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Is this the active profile? (only one per user)",
    )

    template_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personality_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="Template this profile is based on",
    )

    traits: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Personality traits (formality, humor, strictness, empathy, verbosity)",
    )

    rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Custom rules array",
    )

    voice_style: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Voice configuration (TTS parameters)",
    )

    custom_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text additional instructions",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="personality_profiles",
        lazy="selectin",
    )

    template: Mapped["PersonalityTemplate | None"] = relationship(
        back_populates="profiles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the personality profile."""
        return f"<PersonalityProfile(id={self.id}, name={self.name!r}, active={self.is_active})>"
