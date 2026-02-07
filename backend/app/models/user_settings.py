"""UserSettings model."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User

# Default settings for new users
DEFAULT_SETTINGS = {
    "adhs_mode": True,
    "nudge_intensity": "medium",
    "auto_breakdown": True,
    "gamification_enabled": True,
    "focus_timer_minutes": 25,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "preferred_reminder_times": ["09:00", "14:00", "18:00"],
    "expo_push_token": None,
    "notifications_enabled": True,
    "display_name": None,
    "onboarding_complete": False,
    "api_keys": {},  # Encrypted API keys: {"anthropic": "encrypted...", "elevenlabs": "encrypted...", "deepgram": "encrypted..."}
    "stt_provider": "deepgram",  # Default STT provider
    "tts_provider": "elevenlabs",  # Default TTS provider
}


class UserSettings(BaseModel):
    """ADHS-specific user settings stored as JSONB."""

    __tablename__ = "user_settings"
    __table_args__ = {"comment": "ADHS-specific user settings"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User who owns these settings",
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=False,
        server_default=(
            '{"adhs_mode": true, "nudge_intensity": "medium", "auto_breakdown": true, '
            '"gamification_enabled": true, "focus_timer_minutes": 25, '
            '"quiet_hours_start": "22:00", "quiet_hours_end": "07:00", '
            '"preferred_reminder_times": ["09:00", "14:00", "18:00"]}'
        ),
        comment="JSONB settings blob",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="user_settings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserSettings(user_id={self.user_id})>"
