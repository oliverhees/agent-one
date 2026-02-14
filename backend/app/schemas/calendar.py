"""Pydantic schemas for calendar endpoints."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class CalendarEventResponse(BaseModel):
    """Response schema for a calendar event."""

    id: str
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    is_all_day: bool
    calendar_provider: str
    raw_data: dict[str, Any] = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class CalendarEventListResponse(BaseModel):
    """Response schema for a list of calendar events."""

    events: list[CalendarEventResponse]
    total: int


class CalendarStatusResponse(BaseModel):
    """Response schema for calendar connection status."""

    connected: bool
    provider: str | None = None
    last_synced: datetime | None = None
