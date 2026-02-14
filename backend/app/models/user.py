"""User model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.achievement import UserAchievement
    from app.models.brain_entry import BrainEntry
    from app.models.conversation import Conversation
    from app.models.intervention import Intervention
    from app.models.mentioned_item import MentionedItem
    from app.models.nudge_history import NudgeHistory
    from app.models.personality_profile import PersonalityProfile
    from app.models.refresh_token import RefreshToken
    from app.models.task import Task
    from app.models.user_settings import UserSettings
    from app.models.user_stats import UserStats
    from app.models.briefing import Briefing
    from app.models.wellbeing_score import WellbeingScore
    from app.models.predicted_pattern import PredictedPattern
    from app.models.calendar_event import CalendarEvent
    from app.models.reminder import Reminder
    from app.models.webhook import WebhookConfig
    from app.models.n8n_workflow import N8nWorkflow
    from app.models.trust_score import TrustScore
    from app.models.agent_activity import AgentActivity
    from app.models.approval_request import ApprovalRequest
    from app.models.email_config import EmailConfig
    from app.models.reflexion_log import ReflexionLog


class User(BaseModel):
    """User model representing a registered user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (login)",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt password hash",
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User display name",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to user avatar image",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Is user account active?",
    )

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    brain_entries: Mapped[list["BrainEntry"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    mentioned_items: Mapped[list["MentionedItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    personality_profiles: Mapped[list["PersonalityProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    user_stats: Mapped["UserStats | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    nudges: Mapped[list["NudgeHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    user_settings: Mapped["UserSettings | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    wellbeing_scores: Mapped[list["WellbeingScore"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    interventions: Mapped[list["Intervention"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    briefings: Mapped[list["Briefing"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    predicted_patterns: Mapped[list["PredictedPattern"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    n8n_workflows: Mapped[list["N8nWorkflow"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    trust_scores: Mapped[list["TrustScore"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    agent_activities: Mapped[list["AgentActivity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    email_config: Mapped["EmailConfig | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    reflexion_logs: Mapped[list["ReflexionLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email})>"
