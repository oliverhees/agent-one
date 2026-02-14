"""Pydantic schemas for Morning Briefing API."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class BriefingTaskItem(BaseModel):
    """A single task suggested in a briefing."""

    task_id: str
    title: str
    priority: str
    reason: str | None = None


class BriefingResponse(BaseModel):
    """Response for a single briefing."""

    id: str
    briefing_date: date
    content: str
    tasks_suggested: list[BriefingTaskItem | dict[str, Any]] = Field(default_factory=list)
    wellbeing_snapshot: dict[str, Any] = Field(default_factory=dict)
    status: str
    read_at: datetime | None = None
    created_at: datetime


class BriefingHistoryResponse(BaseModel):
    """Response for briefing history."""

    briefings: list[BriefingResponse] = Field(default_factory=list)
    days: int = Field(ge=1, le=90)


class BrainDumpRequest(BaseModel):
    """Request for brain dump text processing."""

    text: str = Field(min_length=1, max_length=5000, description="Raw brain dump text")


class BrainDumpResponse(BaseModel):
    """Response after processing a brain dump."""

    tasks_created: int
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    message: str
