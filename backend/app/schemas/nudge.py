"""Nudge schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NudgeResponse(BaseModel):
    """Schema for an active nudge response."""

    id: UUID = Field(..., description="Nudge unique identifier")
    task_id: UUID | None = Field(None, description="Related task ID")
    task_title: str | None = Field(None, description="Title of the related task")
    nudge_level: str = Field(..., description="Intensity: gentle, moderate, firm")
    nudge_type: str = Field(..., description="Type: deadline_approaching, overdue, stale, follow_up")
    message: str = Field(..., description="Personalized reminder message")
    delivered_at: datetime = Field(..., description="Delivery timestamp")


class NudgeListResponse(BaseModel):
    """Schema for active nudges list response."""

    nudges: list[NudgeResponse] = Field(..., description="Active (unacknowledged) nudges")
    count: int = Field(..., description="Number of active nudges")


class NudgeAcknowledgeResponse(BaseModel):
    """Schema for nudge acknowledge response."""

    id: UUID = Field(..., description="Nudge ID")
    acknowledged_at: datetime = Field(..., description="Acknowledgement timestamp")


class NudgeHistoryItem(BaseModel):
    """Schema for a single nudge history entry."""

    id: UUID = Field(..., description="Nudge unique identifier")
    task_id: UUID | None = Field(None, description="Related task ID")
    task_title: str | None = Field(None, description="Title of the related task")
    nudge_level: str = Field(..., description="Intensity: gentle, moderate, firm")
    nudge_type: str = Field(..., description="Type: deadline_approaching, overdue, stale, follow_up")
    message: str = Field(..., description="Personalized reminder message")
    delivered_at: datetime = Field(..., description="Delivery timestamp")
    acknowledged_at: datetime | None = Field(None, description="Acknowledgement timestamp")


class NudgeHistoryResponse(BaseModel):
    """Schema for paginated nudge history response."""

    items: list[NudgeHistoryItem] = Field(..., description="Nudge history entries")
    next_cursor: str | None = Field(None, description="Cursor for next page")
    has_more: bool = Field(..., description="More items available")
    total_count: int = Field(..., description="Total number of nudge history entries")
