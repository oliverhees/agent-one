"""Pydantic schemas for n8n Bridge endpoints."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class N8nWorkflowCreate(BaseModel):
    """Request schema for creating an n8n workflow."""

    name: str = Field(max_length=200)
    description: str | None = None
    webhook_url: str = Field(max_length=2000)
    input_schema: dict[str, Any] = Field(default_factory=dict)


class N8nWorkflowUpdate(BaseModel):
    """Request schema for updating an n8n workflow."""

    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    webhook_url: str | None = Field(default=None, max_length=2000)
    input_schema: dict[str, Any] | None = None
    is_active: bool | None = None


class N8nWorkflowResponse(BaseModel):
    """Response schema for an n8n workflow."""

    id: str
    user_id: str
    name: str
    description: str | None = None
    webhook_url: str
    input_schema: dict[str, Any]
    is_active: bool
    execution_count: int
    last_executed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class N8nWorkflowListResponse(BaseModel):
    """Response schema for a list of n8n workflows."""

    workflows: list[N8nWorkflowResponse]
    total: int


class N8nExecuteRequest(BaseModel):
    """Request schema for executing an n8n workflow."""

    input_data: dict[str, Any] = Field(default_factory=dict)


class N8nExecuteResponse(BaseModel):
    """Response schema for n8n workflow execution."""

    workflow_id: str
    success: bool
    response_data: dict[str, Any] = Field(default_factory=dict)
    execution_count: int
