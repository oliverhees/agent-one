"""Task model."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class TaskPriority(str, enum.Enum):
    """Task priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    """Task status enum."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskSource(str, enum.Enum):
    """Task source enum."""

    MANUAL = "manual"
    CHAT_EXTRACT = "chat_extract"
    BREAKDOWN = "breakdown"
    RECURRING = "recurring"


class Task(BaseModel):
    """Task model representing a user task with hierarchy support."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("parent_id != id", name="ck_tasks_no_self_parent"),
        CheckConstraint(
            "completed_at IS NULL OR status = 'done'",
            name="ck_tasks_completed_at_status",
        ),
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_due_date", "user_id", "due_date"),
        Index("ix_tasks_user_status_due", "user_id", "status", "due_date"),
        Index("ix_tasks_tags", "tags", postgresql_using="gin"),
        {"comment": "User tasks with hierarchy support"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this task",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Task title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed task description",
    )

    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="medium",
        comment="Priority: low, medium, high, urgent",
    )

    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="open",
        comment="Status: open, in_progress, done, cancelled",
    )

    due_date: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Due date for the task",
    )

    completed_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when task was completed",
    )

    xp_earned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="XP earned when task was completed",
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent task ID for sub-tasks",
    )

    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Is this a recurring task?",
    )

    recurrence_rule: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="iCal RRULE for recurring tasks",
    )

    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="Tags for categorization",
    )

    source: Mapped[TaskSource] = mapped_column(
        SQLEnum(TaskSource, name="task_source", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="manual",
        comment="Source: manual, chat_extract, breakdown, recurring",
    )

    source_message_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        comment="Message from which this task was extracted",
    )

    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated duration in minutes",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="tasks",
        lazy="selectin",
    )

    parent: Mapped["Task | None"] = relationship(
        back_populates="subtasks",
        remote_side="Task.id",
        lazy="selectin",
    )

    subtasks: Mapped[list["Task"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    source_message: Mapped["Message | None"] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the task."""
        return f"<Task(id={self.id}, title={self.title!r}, status={self.status.value})>"
