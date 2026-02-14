"""Pydantic schemas for reminder endpoints."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    """Request schema for creating a reminder."""

    title: str = Field(max_length=500)
    description: str | None = None
    remind_at: datetime
    source: Literal["manual", "chat", "calendar"] = "manual"
    recurrence: Literal["daily", "weekly", "monthly"] | None = None
    recurrence_end: datetime | None = None
    linked_task_id: str | None = None
    linked_event_id: str | None = None


class ReminderUpdate(BaseModel):
    """Request schema for updating a reminder."""

    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    remind_at: datetime | None = None
    recurrence: Literal["daily", "weekly", "monthly"] | None = None
    recurrence_end: datetime | None = None


class ReminderResponse(BaseModel):
    """Response schema for a reminder."""

    id: str
    user_id: str
    title: str
    description: str | None = None
    remind_at: datetime
    source: str
    status: str
    recurrence: str | None = None
    recurrence_end: datetime | None = None
    linked_task_id: str | None = None
    linked_event_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReminderListResponse(BaseModel):
    """Response schema for a list of reminders."""

    reminders: list[ReminderResponse]
    total: int


class ReminderSnoozeRequest(BaseModel):
    """Request schema for snoozing a reminder."""

    snooze_until: datetime
