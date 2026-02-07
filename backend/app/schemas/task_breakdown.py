"""Task breakdown schemas for request/response validation."""

from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.task import TaskResponse


class BreakdownParentTask(BaseModel):
    """Schema for the parent task in a breakdown response."""

    id: UUID = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    priority: str = Field(..., description="Priority")
    estimated_minutes: int | None = Field(None, description="Estimated duration")


class BreakdownSuggestedSubtask(BaseModel):
    """Schema for a suggested sub-task from AI breakdown."""

    title: str = Field(..., description="Suggested sub-task title")
    description: str = Field(..., description="Suggested description")
    estimated_minutes: int = Field(..., description="Estimated duration in minutes")
    order: int = Field(..., description="Recommended order (1-based)")


class BreakdownResponse(BaseModel):
    """Schema for task breakdown suggestion response."""

    parent_task: BreakdownParentTask = Field(..., description="Parent task summary")
    suggested_subtasks: list[BreakdownSuggestedSubtask] = Field(
        ..., description="3-7 suggested sub-tasks"
    )


class BreakdownConfirmSubtask(BaseModel):
    """Schema for a single sub-task in the confirm request."""

    title: str = Field(..., min_length=1, max_length=500, description="Sub-task title")
    description: str | None = Field(None, max_length=5000, description="Sub-task description")
    estimated_minutes: int | None = Field(None, ge=1, le=1440, description="Estimated duration")


class BreakdownConfirmRequest(BaseModel):
    """Schema for confirming and creating sub-tasks."""

    subtasks: list[BreakdownConfirmSubtask] = Field(
        ..., min_length=1, max_length=10, description="Sub-tasks to create (1-10)"
    )


class BreakdownConfirmParent(BaseModel):
    """Schema for the parent task in a confirm response."""

    id: UUID = Field(..., description="Parent task ID")
    title: str = Field(..., description="Parent task title")
    status: str = Field(..., description="New parent task status")


class BreakdownConfirmResponse(BaseModel):
    """Schema for task breakdown confirm response."""

    parent_task: BreakdownConfirmParent = Field(..., description="Parent task summary")
    created_subtasks: list[TaskResponse] = Field(..., description="Created sub-tasks")
