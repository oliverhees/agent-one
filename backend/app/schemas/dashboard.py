"""Dashboard schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardTask(BaseModel):
    """Schema for a task in the dashboard summary."""

    id: UUID = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    priority: str = Field(..., description="Priority")
    status: str = Field(..., description="Status")
    due_date: datetime | None = Field(None, description="Due date")
    estimated_minutes: int | None = Field(None, description="Estimated duration")


class DashboardGamification(BaseModel):
    """Schema for gamification summary in dashboard."""

    total_xp: int = Field(..., description="Total XP")
    level: int = Field(..., description="Current level")
    streak: int = Field(..., description="Current streak")
    progress_percent: float = Field(..., description="Progress to next level (0.0 - 100.0)")


class DashboardDeadline(BaseModel):
    """Schema for next deadline in dashboard."""

    task_title: str = Field(..., description="Task title")
    due_date: datetime = Field(..., description="Due date")


class DashboardSummaryResponse(BaseModel):
    """Schema for aggregated dashboard summary response."""

    today_tasks: list[DashboardTask] = Field(..., description="Today's tasks (max 10)")
    gamification: DashboardGamification = Field(..., description="Gamification overview")
    next_deadline: DashboardDeadline | None = Field(None, description="Next due task")
    active_nudges_count: int = Field(..., description="Number of active nudges")
    motivational_quote: str = Field(..., description="Context-dependent motivational quote")
