"""Task schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Task title",
        examples=["Arzttermin vereinbaren"],
    )

    description: str | None = Field(
        None,
        max_length=10000,
        description="Detailed task description",
    )

    priority: str | None = Field(
        None,
        description="Task priority: low, medium, high, urgent",
        examples=["medium"],
    )

    due_date: datetime | None = Field(
        None,
        description="Due date for the task",
        examples=["2026-02-10T18:00:00Z"],
    )

    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
        examples=[["wichtig", "gesundheit"]],
    )

    parent_id: UUID | None = Field(
        None,
        description="Parent task ID for sub-tasks",
    )

    estimated_minutes: int | None = Field(
        None,
        ge=1,
        le=1440,
        description="Estimated duration in minutes",
        examples=[30],
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Task title",
    )

    description: str | None = Field(
        None,
        max_length=10000,
        description="Detailed task description",
    )

    priority: str | None = Field(
        None,
        description="Task priority: low, medium, high, urgent",
    )

    status: str | None = Field(
        None,
        description="Task status: open, in_progress, done, cancelled",
    )

    due_date: datetime | None = Field(
        None,
        description="Due date for the task",
    )

    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
    )

    estimated_minutes: int | None = Field(
        None,
        ge=1,
        le=1440,
        description="Estimated duration in minutes",
    )


class TaskResponse(BaseModel):
    """Schema for task response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Task unique identifier")
    user_id: UUID = Field(..., description="User who owns this task")
    title: str = Field(..., description="Task title")
    description: str | None = Field(None, description="Detailed task description")
    priority: str = Field(..., description="Task priority")
    status: str = Field(..., description="Task status")
    due_date: datetime | None = Field(None, description="Due date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    xp_earned: int = Field(..., description="XP earned for this task")
    parent_id: UUID | None = Field(None, description="Parent task ID")
    is_recurring: bool = Field(..., description="Is this a recurring task?")
    recurrence_rule: str | None = Field(None, description="iCal RRULE")
    tags: list[str] = Field(default_factory=list, description="Tags")
    source: str = Field(..., description="Task source")
    source_message_id: UUID | None = Field(None, description="Source message ID")
    estimated_minutes: int | None = Field(None, description="Estimated duration in minutes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TaskCompleteResponse(BaseModel):
    """Schema for task completion response with XP info."""

    model_config = ConfigDict(from_attributes=True)

    task: TaskResponse = Field(..., description="The completed task")
    xp_earned: int = Field(..., description="XP earned for this completion")
    new_total_xp: int = Field(..., description="New total XP after completion")
    level_up: bool = Field(False, description="Did the user level up?")
