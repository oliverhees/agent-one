"""Pydantic schemas for webhook endpoints."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    """Request schema for creating a webhook."""

    name: str = Field(max_length=200)
    url: str = Field(max_length=2000)
    direction: Literal["incoming", "outgoing"]
    events: list[str] = []


class WebhookUpdate(BaseModel):
    """Request schema for updating a webhook."""

    name: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2000)
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    """Response schema for a webhook."""

    id: str
    user_id: str
    name: str
    url: str
    direction: str
    events: list[str] | dict[str, Any]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """Response schema for a list of webhooks."""

    webhooks: list[WebhookResponse]
    total: int


class WebhookLogResponse(BaseModel):
    """Response schema for a webhook log entry."""

    id: str
    webhook_id: str
    direction: str
    event_type: str
    payload: dict[str, Any]
    status_code: int | None = None
    attempt: int
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookLogListResponse(BaseModel):
    """Response schema for a list of webhook logs."""

    logs: list[WebhookLogResponse]
    total: int
