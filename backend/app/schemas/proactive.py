"""Proactive extraction schemas for request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MentionedItemResponse(BaseModel):
    """Schema for mentioned item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Item unique identifier")
    user_id: UUID = Field(..., description="User who owns this item")
    message_id: UUID = Field(..., description="Source message ID")
    item_type: str = Field(..., description="Item type: task, appointment, idea, follow_up, reminder")
    content: str = Field(..., description="Extracted content")
    status: str = Field(..., description="Status: pending, converted, dismissed, snoozed")
    extracted_data: dict[str, Any] = Field(default_factory=dict, description="Structured extracted data")
    converted_to_id: UUID | None = Field(None, description="ID of converted entity")
    converted_to_type: str | None = Field(None, description="Type of converted entity")
    snoozed_until: datetime | None = Field(None, description="Snoozed until timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


class MentionedItemConvertRequest(BaseModel):
    """Schema for converting a mentioned item to a task or brain entry."""

    convert_to: str = Field(
        ...,
        description="Target type: 'task' or 'brain_entry'",
        examples=["task"],
    )
