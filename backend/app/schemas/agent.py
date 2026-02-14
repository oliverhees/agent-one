"""Pydantic schemas for the multi-agent system."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Trust ---
class TrustScoreResponse(BaseModel):
    agent_type: str
    action_type: str
    trust_level: int
    successful_actions: int
    total_actions: int

    model_config = {"from_attributes": True}


class TrustOverview(BaseModel):
    scores: list[TrustScoreResponse]


class TrustUpdateRequest(BaseModel):
    agent_type: str
    trust_level: int = Field(ge=1, le=3)


# --- Agent Activity ---
class AgentActivityResponse(BaseModel):
    id: UUID
    agent_type: str
    action: str
    status: str
    details: dict | None = None
    result: str | None = None
    duration_ms: int | None = None
    error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Approval ---
class ApprovalRequestResponse(BaseModel):
    id: UUID
    agent_type: str
    action: str
    action_details: dict
    status: str
    timeout_seconds: int
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    approved: bool
    reason: str | None = None


# --- Email Config ---
class EmailConfigCreate(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    imap_host: str
    imap_port: int = 993
    imap_user: str
    imap_password: str


class EmailConfigResponse(BaseModel):
    id: UUID
    smtp_host: str
    smtp_port: int
    smtp_user: str
    imap_host: str
    imap_port: int
    imap_user: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Agent Chat ---
class AgentChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None


class AgentChatResponse(BaseModel):
    conversation_id: UUID
    response: str
    agent_actions: list[AgentActivityResponse] = Field(default_factory=list)
    pending_approvals: list[ApprovalRequestResponse] = Field(default_factory=list)
