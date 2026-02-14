# Milestone 6: Multi-Agent & Trust System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the existing raw-httpx AI layer (ai.py/chat.py tool loop) with a LangGraph-based multi-agent system featuring 4 sub-agents (Email/SMTP, Calendar, Research/Tavily, Briefing), 3-level progressive trust, approval gates, SSE activity feed, and reflexion framework.

**Architecture:** LangGraph StateGraph as central supervisor orchestrating sub-agent nodes with timeout isolation. Each sub-agent is a LangGraph node with its own system prompt calling Claude via langchain-anthropic. Trust gates use LangGraph `interrupt()` for human-in-the-loop approval. SSE endpoint streams agent activity to the mobile app. Feature-flag migration — old and new system coexist until stable.

**Tech Stack:** LangGraph, langchain-anthropic, langchain-community, tavily-python, aiosmtplib, aioimaplib, FastAPI SSE (sse-starlette), PostgreSQL, SQLAlchemy 2.0, Pydantic v2

**Design Doc:** `docs/plans/2026-02-14-milestone6-multi-agent-trust-design.md`

---

## Task 1: Install Dependencies

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/pyproject.toml` (if deps listed there too)

**Step 1: Add new dependencies to requirements.txt**

Append these lines to `backend/requirements.txt`:

```
# LangGraph Multi-Agent System
langgraph>=0.3,<1.0
langchain-anthropic>=0.3,<1.0
langchain-community>=0.3,<1.0
langchain-core>=0.3,<1.0

# Research Agent
tavily-python>=0.5,<1.0

# Email Agent (async SMTP/IMAP)
aiosmtplib>=3.0,<4.0
aioimaplib>=2.0,<3.0

# SSE Streaming
sse-starlette>=2.0,<3.0
```

**Step 2: Install and verify**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && pip install -r requirements.txt`
Expected: All packages install successfully, no conflicts.

**Step 3: Verify imports work**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -c "from langgraph.graph import StateGraph; from langchain_anthropic import ChatAnthropic; from tavily import TavilyClient; import aiosmtplib; import sse_starlette; print('All imports OK')"`
Expected: "All imports OK"

**Step 4: Add config settings**

Add to `backend/app/core/config.py` in the Settings class:

```python
    # Tavily Research API
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # LangGraph Feature Flag
    use_langgraph: bool = Field(default=False, alias="USE_LANGGRAPH")
```

**Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/core/config.py
git commit -m "feat(agents): add LangGraph, Tavily, SMTP, SSE dependencies and config"
```

---

## Task 2: Database Models (5 new tables)

**Files:**
- Create: `backend/app/models/trust_score.py`
- Create: `backend/app/models/agent_activity.py`
- Create: `backend/app/models/approval_request.py`
- Create: `backend/app/models/email_config.py`
- Create: `backend/app/models/reflexion_log.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py`

**Step 1: Write tests for models**

Create `backend/tests/test_agent_models.py`:

```python
"""Tests for Milestone 6 agent database models."""

import pytest
import pytest_asyncio
from uuid import uuid4

from app.models.trust_score import TrustScore
from app.models.agent_activity import AgentActivity, AgentActivityStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.email_config import EmailConfig
from app.models.reflexion_log import ReflexionLog, ReflexionOutcome


@pytest.mark.asyncio
async def test_trust_score_creation(db_session):
    user_id = uuid4()
    score = TrustScore(
        user_id=user_id,
        agent_type="email",
        action_type="read",
        trust_level=1,
        successful_actions=0,
        total_actions=0,
    )
    db_session.add(score)
    await db_session.flush()
    assert score.id is not None
    assert score.trust_level == 1


@pytest.mark.asyncio
async def test_agent_activity_creation(db_session):
    user_id = uuid4()
    activity = AgentActivity(
        user_id=user_id,
        agent_type="email",
        action="email_read",
        status=AgentActivityStatus.STARTED,
        details={"folder": "inbox"},
    )
    db_session.add(activity)
    await db_session.flush()
    assert activity.id is not None


@pytest.mark.asyncio
async def test_approval_request_creation(db_session):
    user_id = uuid4()
    request = ApprovalRequest(
        user_id=user_id,
        agent_type="email",
        action="email_send",
        action_details={"to": "test@example.com", "subject": "Test"},
        status=ApprovalStatus.PENDING,
        timeout_seconds=300,
    )
    db_session.add(request)
    await db_session.flush()
    assert request.status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_email_config_creation(db_session):
    user_id = uuid4()
    config = EmailConfig(
        user_id=user_id,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="test@gmail.com",
        smtp_password_encrypted="encrypted_value",
        imap_host="imap.gmail.com",
        imap_port=993,
        imap_user="test@gmail.com",
        imap_password_encrypted="encrypted_value",
        is_active=True,
    )
    db_session.add(config)
    await db_session.flush()
    assert config.id is not None


@pytest.mark.asyncio
async def test_reflexion_log_creation(db_session):
    user_id = uuid4()
    log = ReflexionLog(
        user_id=user_id,
        agent_type="email",
        action="email_send",
        outcome=ReflexionOutcome.APPROVED,
        lesson="User prefers formal subject lines for work emails",
        context={"to": "chef@firma.de"},
    )
    db_session.add(log)
    await db_session.flush()
    assert log.outcome == ReflexionOutcome.APPROVED
```

**Step 2: Create TrustScore model**

Create `backend/app/models/trust_score.py`:

```python
"""TrustScore model for progressive agent autonomy."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class TrustScore(BaseModel):
    """Trust score per user/agent/action combination."""

    __tablename__ = "trust_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "agent_type", "action_type", name="uq_trust_user_agent_action"),
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="email, calendar, research, briefing"
    )

    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="read, write, delete, send"
    )

    trust_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="1=new, 2=trusted, 3=autonomous"
    )

    successful_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_escalation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_violation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="trust_scores")
```

**Step 3: Create AgentActivity model**

Create `backend/app/models/agent_activity.py`:

```python
"""AgentActivity model for logging agent actions (SSE feed source)."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AgentActivityStatus(str, enum.Enum):
    STARTED = "started"
    THINKING = "thinking"
    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class AgentActivity(BaseModel):
    """Log of every agent action for activity feed and audit trail."""

    __tablename__ = "agent_activities"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentActivityStatus] = mapped_column(nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="agent_activities")
```

**Step 4: Create ApprovalRequest model**

Create `backend/app/models/approval_request.py`:

```python
"""ApprovalRequest model for human-in-the-loop approval gates."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Pending approval request for agent actions requiring user consent."""

    __tablename__ = "approval_requests"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    action_details: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(nullable=False, default=ApprovalStatus.PENDING)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    thread_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="LangGraph thread_id for resume"
    )

    user: Mapped["User"] = relationship(back_populates="approval_requests")
```

**Step 5: Create EmailConfig model**

Create `backend/app/models/email_config.py`:

```python
"""EmailConfig model for per-user SMTP/IMAP settings."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class EmailConfig(BaseModel):
    """User email configuration with encrypted credentials."""

    __tablename__ = "email_configs"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_user: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_password_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)

    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993)
    imap_user: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_password_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="email_config")
```

**Step 6: Create ReflexionLog model**

Create `backend/app/models/reflexion_log.py`:

```python
"""ReflexionLog model for agent learning from action outcomes."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ReflexionOutcome(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SUCCESS = "success"


class ReflexionLog(BaseModel):
    """Records agent reflexions and lessons learned per action."""

    __tablename__ = "reflexion_logs"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[ReflexionOutcome] = mapped_column(nullable=False)
    lesson: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="reflexion_logs")
```

**Step 7: Update models/__init__.py**

Add to `backend/app/models/__init__.py`:

```python
from app.models.trust_score import TrustScore
from app.models.agent_activity import AgentActivity, AgentActivityStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.email_config import EmailConfig
from app.models.reflexion_log import ReflexionLog, ReflexionOutcome
```

And add to `__all__`:
```python
    "TrustScore",
    "AgentActivity",
    "AgentActivityStatus",
    "ApprovalRequest",
    "ApprovalStatus",
    "EmailConfig",
    "ReflexionLog",
    "ReflexionOutcome",
```

**Step 8: Update User model relationships**

Add to `backend/app/models/user.py` in TYPE_CHECKING block:
```python
    from app.models.trust_score import TrustScore
    from app.models.agent_activity import AgentActivity
    from app.models.approval_request import ApprovalRequest
    from app.models.email_config import EmailConfig
    from app.models.reflexion_log import ReflexionLog
```

Add relationships:
```python
    trust_scores: Mapped[list["TrustScore"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
    agent_activities: Mapped[list["AgentActivity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
    email_config: Mapped["EmailConfig | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin",
    )
    reflexion_logs: Mapped[list["ReflexionLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
```

**Step 9: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_agent_models.py -v`
Expected: All 5 tests PASS

**Step 10: Commit**

```bash
git add backend/app/models/ backend/tests/test_agent_models.py
git commit -m "feat(agents): add 5 new DB models for multi-agent system"
```

---

## Task 3: Alembic Migration 009

**Files:**
- Create: `backend/alembic/versions/009_phase11_agents.py`

**Step 1: Create migration**

Create `backend/alembic/versions/009_phase11_agents.py`:

```python
"""Phase 11: Multi-Agent & Trust System tables.

Revision ID: 009
Revises: 008
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Trust Scores
    op.create_table(
        "trust_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("trust_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("successful_actions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_actions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_escalation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_violation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "agent_type", "action_type", name="uq_trust_user_agent_action"),
    )

    # Agent Activities
    op.create_table(
        "agent_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("details", JSON, nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_activities_created_at", "agent_activities", ["user_id", "created_at"])

    # Approval Requests
    op.create_table(
        "approval_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("action_details", JSON, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_reason", sa.Text(), nullable=True),
        sa.Column("thread_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Email Configs
    op.create_table(
        "email_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("smtp_host", sa.String(255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_user", sa.String(255), nullable=False),
        sa.Column("smtp_password_encrypted", sa.String(500), nullable=False),
        sa.Column("imap_host", sa.String(255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"),
        sa.Column("imap_user", sa.String(255), nullable=False),
        sa.Column("imap_password_encrypted", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Reflexion Logs
    op.create_table(
        "reflexion_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("lesson", sa.Text(), nullable=True),
        sa.Column("context", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reflexion_logs")
    op.drop_table("email_configs")
    op.drop_table("approval_requests")
    op.drop_index("ix_agent_activities_created_at", "agent_activities")
    op.drop_table("agent_activities")
    op.drop_table("trust_scores")
```

**Step 2: Commit**

```bash
git add backend/alembic/versions/009_phase11_agents.py
git commit -m "db(agents): add migration 009 for multi-agent tables"
```

---

## Task 4: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/agent.py`

**Step 1: Create schemas**

Create `backend/app/schemas/agent.py`:

```python
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
```

**Step 2: Commit**

```bash
git add backend/app/schemas/agent.py
git commit -m "feat(agents): add Pydantic schemas for agent system"
```

---

## Task 5: TrustService

**Files:**
- Create: `backend/app/services/trust.py`
- Create: `backend/tests/test_trust_service.py`

**Step 1: Write tests**

Create `backend/tests/test_trust_service.py`:

```python
"""Tests for TrustService."""

import pytest
from uuid import uuid4

from app.services.trust import TrustService


@pytest.mark.asyncio
async def test_get_trust_level_default(db_session):
    """New user/agent combo should return level 1."""
    service = TrustService(db_session)
    level = await service.get_trust_level(str(uuid4()), "email", "read")
    assert level == 1


@pytest.mark.asyncio
async def test_requires_approval_level1(db_session):
    """Level 1: all actions require approval."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    assert await service.requires_approval(user_id, "email", "read") is True
    assert await service.requires_approval(user_id, "email", "send") is True


@pytest.mark.asyncio
async def test_record_action_increments(db_session):
    """Recording an action should increment counters."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.successful_actions == 1
    assert score.total_actions == 1


@pytest.mark.asyncio
async def test_auto_escalation_level1_to_level2(db_session):
    """After 10 successful actions, trust should escalate from 1 to 2."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    for _ in range(10):
        await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.trust_level == 2


@pytest.mark.asyncio
async def test_no_auto_escalation_to_level3(db_session):
    """Level 3 requires explicit user opt-in, not auto-escalation."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    for _ in range(50):
        await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.trust_level == 2  # not 3


@pytest.mark.asyncio
async def test_manual_set_level3(db_session):
    """User can manually set trust level to 3."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    await service.set_trust_level(user_id, "email", "send", 3)
    level = await service.get_trust_level(user_id, "email", "send")
    assert level == 3


@pytest.mark.asyncio
async def test_downgrade_on_rejection(db_session):
    """Rejection should downgrade level 3 to 2."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    await service.set_trust_level(user_id, "email", "send", 3)
    await service.record_violation(user_id, "email", "send")
    level = await service.get_trust_level(user_id, "email", "send")
    assert level == 2


@pytest.mark.asyncio
async def test_level2_read_auto_write_approval(db_session):
    """Level 2: read=auto, write/send=approval."""
    service = TrustService(db_session)
    user_id = str(uuid4())
    await service.set_trust_level(user_id, "email", "read", 2)
    await service.set_trust_level(user_id, "email", "send", 2)
    assert await service.requires_approval(user_id, "email", "read") is False
    assert await service.requires_approval(user_id, "email", "send") is True
```

**Step 2: Implement TrustService**

Create `backend/app/services/trust.py`:

```python
"""Trust service for progressive agent autonomy."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trust_score import TrustScore

ESCALATION_THRESHOLD = 10  # successful actions needed for level 1 -> 2
READ_ACTIONS = {"read", "list", "search", "summarize", "analyze"}
WRITE_ACTIONS = {"write", "send", "create", "update", "delete", "draft"}


class TrustService:
    """Manages trust levels for agent actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_score(self, user_id: str, agent_type: str, action_type: str) -> TrustScore:
        stmt = select(TrustScore).where(
            TrustScore.user_id == UUID(user_id),
            TrustScore.agent_type == agent_type,
            TrustScore.action_type == action_type,
        )
        result = await self.db.execute(stmt)
        score = result.scalar_one_or_none()
        if not score:
            score = TrustScore(
                user_id=UUID(user_id),
                agent_type=agent_type,
                action_type=action_type,
                trust_level=1,
                successful_actions=0,
                total_actions=0,
            )
            self.db.add(score)
            await self.db.flush()
            await self.db.refresh(score)
        return score

    async def get_trust_level(self, user_id: str, agent_type: str, action_type: str) -> int:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        return score.trust_level

    async def requires_approval(self, user_id: str, agent_type: str, action_type: str) -> bool:
        level = await self.get_trust_level(user_id, agent_type, action_type)
        if level >= 3:
            return False
        if level >= 2 and action_type in READ_ACTIONS:
            return False
        return True

    async def record_action(self, user_id: str, agent_type: str, action_type: str, success: bool) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        score.total_actions += 1
        if success:
            score.successful_actions += 1
        # Auto-escalate 1 -> 2 after threshold
        if score.trust_level == 1 and score.successful_actions >= ESCALATION_THRESHOLD:
            score.trust_level = 2
            score.last_escalation_at = datetime.now(timezone.utc)
        await self.db.flush()
        return score

    async def set_trust_level(self, user_id: str, agent_type: str, action_type: str, level: int) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        score.trust_level = max(1, min(3, level))
        if level > score.trust_level:
            score.last_escalation_at = datetime.now(timezone.utc)
        await self.db.flush()
        return score

    async def record_violation(self, user_id: str, agent_type: str, action_type: str) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        score.last_violation_at = datetime.now(timezone.utc)
        if score.trust_level == 3:
            score.trust_level = 2
        await self.db.flush()
        return score

    async def get_all_scores(self, user_id: str) -> list[TrustScore]:
        stmt = select(TrustScore).where(TrustScore.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

**Step 3: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_trust_service.py -v`
Expected: All 8 tests PASS

**Step 4: Commit**

```bash
git add backend/app/services/trust.py backend/tests/test_trust_service.py
git commit -m "feat(agents): implement TrustService with 3-level progressive autonomy"
```

---

## Task 6: LangGraph Agent State & Supervisor

**Files:**
- Create: `backend/app/agents/__init__.py`
- Create: `backend/app/agents/state.py`
- Create: `backend/app/agents/supervisor.py`
- Create: `backend/app/agents/tools.py`
- Create: `backend/tests/test_agent_supervisor.py`

**Step 1: Create agent package**

Create `backend/app/agents/__init__.py`:

```python
"""LangGraph multi-agent system for ALICE."""
```

**Step 2: Define AgentState**

Create `backend/app/agents/state.py`:

```python
"""Agent state definition for LangGraph."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State flowing through the entire LangGraph supervisor."""

    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str

    # Routing
    next_agent: str | None
    agent_plan: list[str]

    # Trust
    trust_level: int
    requires_approval: bool
    pending_action: dict | None

    # Execution
    agent_results: list[dict]
    current_agent: str | None
    error: str | None

    # Context
    memory_context: str | None
    user_preferences: dict
    system_prompt: str
```

**Step 3: Migrate existing tools to LangChain format**

Create `backend/app/agents/tools.py`:

```python
"""Existing ALICE tools converted to LangChain tool format.

These wrap the existing tool executor functions from chat.py
so they can be used within LangGraph sub-agent nodes.
"""

import json
from typing import Any
from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession


class AliceToolkit:
    """Wrapper providing existing ALICE tools as LangChain tools."""

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self._executor = None

    async def _get_executor(self):
        """Lazy-load the tool executor from ChatService."""
        if self._executor is None:
            from app.services.chat import ChatService
            chat_service = ChatService(self.db)
            self._executor = await chat_service._create_tool_executor(self.user_id)
        return self._executor

    async def execute(self, tool_name: str, tool_input: dict) -> str:
        """Execute a legacy ALICE tool by name."""
        executor = await self._get_executor()
        return await executor(tool_name, tool_input)

    def get_tool_definitions(self) -> list[dict]:
        """Return the original ALICE_TOOLS definitions."""
        from app.services.ai import ALICE_TOOLS
        return ALICE_TOOLS
```

**Step 4: Build the Supervisor**

Create `backend/app/agents/supervisor.py`:

```python
"""LangGraph Supervisor — central orchestration graph for ALICE agents."""

import asyncio
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

AGENT_TYPES = ["email", "calendar", "research", "briefing"]

ROUTING_PROMPT = """Du bist der ALICE Supervisor. Analysiere die User-Nachricht und entscheide:

1. Braucht es einen Sub-Agent? Wenn ja, welchen?
   - "email": Fuer alles rund um Emails (lesen, schreiben, senden)
   - "calendar": Fuer Termine und Kalender-Operationen
   - "research": Fuer Web-Recherche und Informationssuche
   - "briefing": Fuer Tagesbriefings und Brain Dump Zusammenfassungen
   - "direct": Fuer direkte Antworten ohne Agent (Chat, Aufgaben, Brain, etc.)

2. Wenn ein Agent noetig ist, welche Aktion soll er ausfuehren?

Antworte NUR mit JSON:
{"agent": "email|calendar|research|briefing|direct", "action": "action_name", "reason": "kurze Begruendung"}
"""


async def safe_node(node_fn, state: AgentState, timeout_s: float, agent_name: str) -> AgentState:
    """Execute a node with timeout protection."""
    try:
        result = await asyncio.wait_for(node_fn(state), timeout=timeout_s)
        return result
    except asyncio.TimeoutError:
        logger.error("%s timed out after %ss", agent_name, timeout_s)
        return {
            **state,
            "error": f"{agent_name} Timeout nach {timeout_s}s",
            "current_agent": None,
            "next_agent": None,
        }
    except Exception as e:
        logger.error("%s failed: %s", agent_name, e)
        return {
            **state,
            "error": f"{agent_name} Fehler: {str(e)}",
            "current_agent": None,
            "next_agent": None,
        }


def build_supervisor_graph() -> StateGraph:
    """Build the main ALICE supervisor graph.

    Returns a compiled StateGraph. Call with:
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "..."}})
    """
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    async def context_loader(state: AgentState) -> dict:
        """Load memory context and user preferences."""
        # Memory context is pre-loaded by the API layer
        return {"current_agent": "supervisor"}

    async def supervisor_node(state: AgentState) -> dict:
        """Route to the appropriate sub-agent or respond directly."""
        import json as json_mod

        messages = state["messages"]
        system = state.get("system_prompt", "Du bist ALICE.")

        routing_messages = [
            SystemMessage(content=ROUTING_PROMPT + "\n\n" + system),
            *messages[-5:],  # last 5 messages for context
        ]

        response = await llm.ainvoke(routing_messages)
        text = response.content if isinstance(response.content, str) else str(response.content)

        try:
            # Extract JSON from response
            start = text.index("{")
            end = text.rindex("}") + 1
            decision = json_mod.loads(text[start:end])
            agent = decision.get("agent", "direct")
            action = decision.get("action", "")
        except (ValueError, json_mod.JSONDecodeError):
            agent = "direct"
            action = ""

        if agent == "direct" or agent not in AGENT_TYPES:
            return {
                "next_agent": None,
                "current_agent": None,
                "pending_action": None,
            }

        return {
            "next_agent": agent,
            "current_agent": agent,
            "pending_action": {"agent": agent, "action": action},
        }

    async def direct_response(state: AgentState) -> dict:
        """Generate a direct response using existing tools (no sub-agent)."""
        messages = state["messages"]
        system = state.get("system_prompt", "Du bist ALICE.")

        response = await llm.ainvoke(
            [SystemMessage(content=system)] + messages
        )

        return {
            "messages": [response],
            "next_agent": None,
            "current_agent": None,
        }

    async def response_node(state: AgentState) -> dict:
        """Final response aggregation — summarize agent results for user."""
        results = state.get("agent_results", [])
        error = state.get("error")

        if error:
            return {
                "messages": [AIMessage(content=f"Es gab ein Problem: {error}")],
            }

        if not results:
            # Fallback: direct LLM response
            return await direct_response(state)

        # Let LLM summarize agent results for user
        result_text = "\n".join(
            f"- {r.get('agent', '?')}: {r.get('summary', r.get('result', '?'))}"
            for r in results
        )
        summary_messages = [
            SystemMessage(content=state.get("system_prompt", "Du bist ALICE.")),
            *state["messages"],
            HumanMessage(content=f"[SYSTEM] Agent-Ergebnisse:\n{result_text}\n\nFasse die Ergebnisse fuer den User zusammen."),
        ]
        response = await llm.ainvoke(summary_messages)
        return {"messages": [response]}

    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("context_loader", context_loader)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("direct_response", direct_response)
    graph.add_node("response_node", response_node)

    # Edges
    graph.add_edge(START, "context_loader")
    graph.add_edge("context_loader", "supervisor")

    # Conditional routing from supervisor
    def route_supervisor(state: AgentState) -> str:
        next_agent = state.get("next_agent")
        if next_agent and next_agent in AGENT_TYPES:
            return next_agent
        return "direct_response"

    # For now, route to direct_response for all agents (sub-agents added in later tasks)
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {agent: "direct_response" for agent in AGENT_TYPES} | {"direct_response": "direct_response"},
    )

    graph.add_edge("direct_response", "response_node")
    graph.add_edge("response_node", END)

    return graph


def create_agent(checkpointer=None):
    """Create and compile the supervisor agent."""
    graph = build_supervisor_graph()
    if checkpointer is None:
        checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

**Step 5: Write supervisor test**

Create `backend/tests/test_agent_supervisor.py`:

```python
"""Tests for LangGraph supervisor graph structure."""

import pytest
from unittest.mock import patch, AsyncMock

from app.agents.state import AgentState
from app.agents.supervisor import build_supervisor_graph, AGENT_TYPES


def test_graph_structure():
    """Supervisor graph should have required nodes and edges."""
    graph = build_supervisor_graph()
    compiled = graph.compile()
    # Graph should compile without errors
    assert compiled is not None


def test_agent_types_defined():
    """All 4 agent types should be defined."""
    assert "email" in AGENT_TYPES
    assert "calendar" in AGENT_TYPES
    assert "research" in AGENT_TYPES
    assert "briefing" in AGENT_TYPES
    assert len(AGENT_TYPES) == 4


def test_agent_state_fields():
    """AgentState should have all required fields."""
    state: AgentState = {
        "messages": [],
        "user_id": "test",
        "next_agent": None,
        "agent_plan": [],
        "trust_level": 1,
        "requires_approval": False,
        "pending_action": None,
        "agent_results": [],
        "current_agent": None,
        "error": None,
        "memory_context": None,
        "user_preferences": {},
        "system_prompt": "test",
    }
    assert state["trust_level"] == 1
    assert state["user_id"] == "test"
```

**Step 6: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_agent_supervisor.py -v`
Expected: All 3 tests PASS

**Step 7: Commit**

```bash
git add backend/app/agents/ backend/tests/test_agent_supervisor.py
git commit -m "feat(agents): implement LangGraph supervisor graph with state and tools wrapper"
```

---

## Task 7: Email Sub-Agent (SMTP/IMAP)

**Files:**
- Create: `backend/app/agents/nodes/__init__.py`
- Create: `backend/app/agents/nodes/email_agent.py`
- Create: `backend/app/services/email.py`
- Create: `backend/tests/test_email_service.py`

**Step 1: Write email service tests**

Create `backend/tests/test_email_service.py`:

```python
"""Tests for EmailService (SMTP/IMAP)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.email import EmailService


@pytest.mark.asyncio
async def test_send_email_success(db_session):
    """Should send email via SMTP."""
    service = EmailService(db_session)
    with patch("app.services.email.aiosmtplib") as mock_smtp:
        mock_client = AsyncMock()
        mock_smtp.SMTP.return_value = mock_client
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.login = AsyncMock()
        mock_client.send_message = AsyncMock()

        result = await service.send_email(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="pass",
            to="recipient@test.com",
            subject="Test",
            body="Hello",
        )
        assert result["success"] is True


@pytest.mark.asyncio
async def test_send_email_timeout():
    """Should handle SMTP timeout gracefully."""
    service = EmailService(None)
    with patch("app.services.email.aiosmtplib") as mock_smtp:
        mock_smtp.SMTP.side_effect = TimeoutError("Connection timed out")

        result = await service.send_email(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="pass",
            to="recipient@test.com",
            subject="Test",
            body="Hello",
        )
        assert result["success"] is False
        assert "error" in result
```

**Step 2: Implement EmailService**

Create `backend/app/services/email.py`:

```python
"""Email service for SMTP sending and IMAP reading."""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from uuid import UUID

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_value, decrypt_value
from app.models.email_config import EmailConfig

logger = logging.getLogger(__name__)


class EmailService:
    """Async email operations via SMTP/IMAP."""

    def __init__(self, db: AsyncSession | None):
        self.db = db

    async def get_config(self, user_id: str) -> EmailConfig | None:
        if not self.db:
            return None
        stmt = select(EmailConfig).where(
            EmailConfig.user_id == UUID(user_id), EmailConfig.is_active == True
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def send_email(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        to: str,
        subject: str,
        body: str,
        reply_to: str | None = None,
    ) -> dict:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to
            msg["Subject"] = subject
            if reply_to:
                msg["In-Reply-To"] = reply_to
            msg.attach(MIMEText(body, "plain", "utf-8"))

            async with aiosmtplib.SMTP(
                hostname=smtp_host, port=smtp_port, use_tls=False, start_tls=True
            ) as client:
                await client.login(smtp_user, smtp_password)
                await client.send_message(msg)

            return {"success": True, "to": to, "subject": subject}
        except Exception as e:
            logger.error("SMTP send failed: %s", e)
            return {"success": False, "error": str(e)}

    async def read_emails(
        self,
        imap_host: str,
        imap_port: int,
        imap_user: str,
        imap_password: str,
        folder: str = "INBOX",
        limit: int = 10,
    ) -> dict:
        try:
            import aioimaplib
            client = aioimaplib.IMAP4_SSL(host=imap_host, port=imap_port)
            await client.wait_hello_from_server()
            await client.login(imap_user, imap_password)
            await client.select(folder)

            _, data = await client.search("ALL")
            message_ids = data[0].split()[-limit:]

            emails = []
            for msg_id in message_ids:
                _, msg_data = await client.fetch(msg_id.decode(), "(RFC822)")
                if msg_data:
                    emails.append({"id": msg_id.decode(), "raw": str(msg_data)[:500]})

            await client.logout()
            return {"success": True, "count": len(emails), "emails": emails}
        except Exception as e:
            logger.error("IMAP read failed: %s", e)
            return {"success": False, "error": str(e)}

    async def save_config(
        self, user_id: str, smtp_host: str, smtp_port: int, smtp_user: str,
        smtp_password: str, imap_host: str, imap_port: int, imap_user: str,
        imap_password: str,
    ) -> EmailConfig:
        existing = await self.get_config(user_id)
        if existing:
            existing.smtp_host = smtp_host
            existing.smtp_port = smtp_port
            existing.smtp_user = smtp_user
            existing.smtp_password_encrypted = encrypt_value(smtp_password)
            existing.imap_host = imap_host
            existing.imap_port = imap_port
            existing.imap_user = imap_user
            existing.imap_password_encrypted = encrypt_value(imap_password)
            await self.db.flush()
            return existing

        config = EmailConfig(
            user_id=UUID(user_id),
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password_encrypted=encrypt_value(smtp_password),
            imap_host=imap_host,
            imap_port=imap_port,
            imap_user=imap_user,
            imap_password_encrypted=encrypt_value(imap_password),
            is_active=True,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config
```

**Step 3: Create Email Agent Node**

Create `backend/app/agents/nodes/__init__.py`:
```python
"""LangGraph agent nodes."""
```

Create `backend/app/agents/nodes/email_agent.py`:

```python
"""Email sub-agent node for LangGraph."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_SYSTEM_PROMPT = """Du bist der ALICE Email-Agent. Du hilfst dem User mit Email-Operationen.

Verfuegbare Aktionen:
- email_read: Emails aus dem Postfach lesen und zusammenfassen
- email_draft: Einen Email-Entwurf erstellen
- email_send: Eine Email versenden
- email_reply: Auf eine Email antworten

Antworte immer auf Deutsch. Fasse Emails ADHS-freundlich zusammen (kurz, strukturiert, Kernpunkte).
"""


async def email_agent_node(state: AgentState) -> dict:
    """Email agent: handles email read/send/draft operations."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    action = state.get("pending_action", {})
    action_name = action.get("action", "email_read")

    messages = [
        SystemMessage(content=EMAIL_SYSTEM_PROMPT),
        *state["messages"][-3:],
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "email",
            "action": action_name,
            "summary": result_text[:200],
            "result": result_text,
        }],
        "current_agent": None,
        "next_agent": None,
        "pending_action": {
            **action,
            "type": "send" if "send" in action_name else "read",
        },
    }
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_email_service.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/email.py backend/app/agents/nodes/ backend/tests/test_email_service.py
git commit -m "feat(agents): implement Email sub-agent with SMTP/IMAP service"
```

---

## Task 8: Research Sub-Agent (Tavily)

**Files:**
- Create: `backend/app/agents/nodes/research_agent.py`
- Create: `backend/app/services/research.py`
- Create: `backend/tests/test_research_service.py`

**Step 1: Write tests**

Create `backend/tests/test_research_service.py`:

```python
"""Tests for ResearchService (Tavily)."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.research import ResearchService


@pytest.mark.asyncio
async def test_search_success():
    service = ResearchService()
    with patch("app.services.research.TavilyClient") as mock_tavily:
        mock_client = MagicMock()
        mock_tavily.return_value = mock_client
        mock_client.search.return_value = {
            "results": [{"title": "Test", "url": "https://test.com", "content": "Result"}]
        }
        result = await service.search("ADHS Strategien")
        assert result["success"] is True
        assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_search_no_api_key():
    service = ResearchService(api_key="")
    result = await service.search("test")
    assert result["success"] is False
    assert "error" in result
```

**Step 2: Implement ResearchService**

Create `backend/app/services/research.py`:

```python
"""Research service using Tavily API for web search."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResearchService:
    """Web search via Tavily API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.tavily_api_key

    async def search(self, query: str, max_results: int = 5) -> dict:
        if not self.api_key:
            return {"success": False, "error": "Tavily API key not configured"}
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.search(query=query, max_results=max_results)
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                }
                for r in response.get("results", [])
            ]
            return {"success": True, "query": query, "results": results}
        except Exception as e:
            logger.error("Tavily search failed: %s", e)
            return {"success": False, "error": str(e)}

    async def extract(self, url: str) -> dict:
        if not self.api_key:
            return {"success": False, "error": "Tavily API key not configured"}
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.extract(urls=[url])
            return {"success": True, "url": url, "content": response}
        except Exception as e:
            logger.error("Tavily extract failed: %s", e)
            return {"success": False, "error": str(e)}
```

**Step 3: Create Research Agent Node**

Create `backend/app/agents/nodes/research_agent.py`:

```python
"""Research sub-agent node for LangGraph."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """Du bist der ALICE Research-Agent. Du hilfst dem User bei Web-Recherchen.

Verfuegbare Aktionen:
- web_search: Suche im Internet nach Informationen
- web_extract: Extrahiere Inhalte einer bestimmten Webseite
- summarize_results: Fasse Suchergebnisse ADHS-freundlich zusammen

Antworte immer auf Deutsch. Strukturiere Ergebnisse klar mit Aufzaehlungen.
"""


async def research_agent_node(state: AgentState) -> dict:
    """Research agent: web search and content extraction."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    action = state.get("pending_action", {})

    messages = [
        SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
        *state["messages"][-3:],
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "research",
            "action": action.get("action", "web_search"),
            "summary": result_text[:200],
            "result": result_text,
        }],
        "current_agent": None,
        "next_agent": None,
        "pending_action": {**action, "type": "read"},
    }
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_research_service.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/research.py backend/app/agents/nodes/research_agent.py backend/tests/test_research_service.py
git commit -m "feat(agents): implement Research sub-agent with Tavily search"
```

---

## Task 9: Calendar & Briefing Sub-Agent Nodes

**Files:**
- Create: `backend/app/agents/nodes/calendar_agent.py`
- Create: `backend/app/agents/nodes/briefing_agent.py`

**Step 1: Create Calendar Agent Node**

Create `backend/app/agents/nodes/calendar_agent.py`:

```python
"""Calendar sub-agent node for LangGraph."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

CALENDAR_SYSTEM_PROMPT = """Du bist der ALICE Calendar-Agent. Du verwaltest Termine fuer den User.

Verfuegbare Aktionen:
- calendar_list_events: Termine anzeigen
- calendar_create_event: Neuen Termin erstellen
- calendar_update_event: Termin aendern
- calendar_delete_event: Termin loeschen

Antworte immer auf Deutsch. Zeige Termine uebersichtlich mit Datum, Uhrzeit und Titel.
"""


async def calendar_agent_node(state: AgentState) -> dict:
    """Calendar agent: manages calendar events."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    action = state.get("pending_action", {})
    action_name = action.get("action", "calendar_list_events")

    messages = [
        SystemMessage(content=CALENDAR_SYSTEM_PROMPT),
        *state["messages"][-3:],
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    action_type = "read" if "list" in action_name else "write"

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "calendar",
            "action": action_name,
            "summary": result_text[:200],
            "result": result_text,
        }],
        "current_agent": None,
        "next_agent": None,
        "pending_action": {**action, "type": action_type},
    }
```

**Step 2: Create Briefing Agent Node**

Create `backend/app/agents/nodes/briefing_agent.py`:

```python
"""Briefing sub-agent node for LangGraph."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

BRIEFING_SYSTEM_PROMPT = """Du bist der ALICE Briefing-Agent. Du erstellst Tagesbriefings und Brain Dump Zusammenfassungen.

Verfuegbare Aktionen:
- generate_briefing: Tagesbriefing mit Terminen, Tasks und Tipps erstellen
- get_brain_dump_summary: Brain Dump Eintraege zusammenfassen

Antworte immer auf Deutsch. ADHS-freundlich: kurz, klar, motivierend.
"""


async def briefing_agent_node(state: AgentState) -> dict:
    """Briefing agent: daily briefings and brain dump summaries."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    action = state.get("pending_action", {})

    messages = [
        SystemMessage(content=BRIEFING_SYSTEM_PROMPT),
        *state["messages"][-3:],
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "briefing",
            "action": action.get("action", "generate_briefing"),
            "summary": result_text[:200],
            "result": result_text,
        }],
        "current_agent": None,
        "next_agent": None,
        "pending_action": {**action, "type": "read"},
    }
```

**Step 3: Wire sub-agents into supervisor**

Update `backend/app/agents/supervisor.py` — replace the conditional edges section:

In the `build_supervisor_graph()` function, after the existing node additions, add:

```python
    from app.agents.nodes.email_agent import email_agent_node
    from app.agents.nodes.calendar_agent import calendar_agent_node
    from app.agents.nodes.research_agent import research_agent_node
    from app.agents.nodes.briefing_agent import briefing_agent_node

    # Sub-agent nodes with timeout wrappers
    async def email_node(state):
        return await safe_node(email_agent_node, state, 30.0, "Email-Agent")

    async def calendar_node(state):
        return await safe_node(calendar_agent_node, state, 15.0, "Calendar-Agent")

    async def research_node(state):
        return await safe_node(research_agent_node, state, 20.0, "Research-Agent")

    async def briefing_node(state):
        return await safe_node(briefing_agent_node, state, 15.0, "Briefing-Agent")

    graph.add_node("email", email_node)
    graph.add_node("calendar", calendar_node)
    graph.add_node("research", research_node)
    graph.add_node("briefing", briefing_node)
```

Replace the conditional edges to route to actual agent nodes:

```python
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "email": "email",
            "calendar": "calendar",
            "research": "research",
            "briefing": "briefing",
            "direct_response": "direct_response",
        },
    )

    # All agent nodes route to response_node
    for agent in AGENT_TYPES:
        graph.add_edge(agent, "response_node")
```

**Step 4: Commit**

```bash
git add backend/app/agents/
git commit -m "feat(agents): add Calendar, Briefing sub-agents and wire all into supervisor"
```

---

## Task 10: Agent API Endpoints

**Files:**
- Create: `backend/app/api/v1/agents.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_agent_api.py`

**Step 1: Write API tests**

Create `backend/tests/test_agent_api.py`:

```python
"""Tests for Agent API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_agent_routes_registered(client):
    """Agent routes should be registered in the API."""
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/agents/trust" in paths
    assert "/api/v1/agents/email/config" in paths
    assert "/api/v1/agents/approvals/pending" in paths


@pytest.mark.asyncio
async def test_get_trust_scores_unauthenticated(client):
    response = await client.get("/api/v1/agents/trust")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_trust_scores_authenticated(auth_client):
    response = await auth_client.get("/api/v1/agents/trust")
    assert response.status_code == 200
    data = response.json()
    assert "scores" in data


@pytest.mark.asyncio
async def test_get_pending_approvals(auth_client):
    response = await auth_client.get("/api/v1/agents/approvals/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_set_trust_level(auth_client):
    response = await auth_client.put(
        "/api/v1/agents/trust",
        json={"agent_type": "email", "trust_level": 2},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_save_email_config(auth_client):
    response = await auth_client.post(
        "/api/v1/agents/email/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "test123",
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "imap_user": "test@gmail.com",
            "imap_password": "test123",
        },
    )
    assert response.status_code == 200
```

**Step 2: Implement Agent API router**

Create `backend/app/api/v1/agents.py`:

```python
"""Agent system API endpoints — trust, approvals, email config, activity."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.user import User
from app.schemas.agent import (
    TrustOverview,
    TrustScoreResponse,
    TrustUpdateRequest,
    ApprovalDecision,
    ApprovalRequestResponse,
    EmailConfigCreate,
    EmailConfigResponse,
    AgentActivityResponse,
)
from app.services.trust import TrustService

router = APIRouter(tags=["Agents"])


@router.get("/trust", response_model=TrustOverview)
async def get_trust_scores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TrustService(db)
    scores = await service.get_all_scores(str(current_user.id))
    return TrustOverview(
        scores=[TrustScoreResponse.model_validate(s) for s in scores]
    )


@router.put("/trust", status_code=status.HTTP_200_OK)
async def set_trust_level(
    data: TrustUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TrustService(db)
    # Set for all action types of this agent
    for action_type in ["read", "write", "send", "delete"]:
        await service.set_trust_level(str(current_user.id), data.agent_type, action_type, data.trust_level)
    await db.commit()
    return {"status": "updated", "agent_type": data.agent_type, "trust_level": data.trust_level}


@router.get("/approvals/pending", response_model=list[ApprovalRequestResponse])
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.user_id == current_user.id,
        ApprovalRequest.status == ApprovalStatus.PENDING,
    ).order_by(ApprovalRequest.created_at.desc())
    result = await db.execute(stmt)
    return [ApprovalRequestResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/approve/{approval_id}")
async def approve_action(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.user_id == current_user.id,
        ApprovalRequest.status == ApprovalStatus.PENDING,
    )
    result = await db.execute(stmt)
    request = result.scalar_one_or_none()
    if not request:
        return {"error": "Approval request not found or already resolved"}

    request.status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED
    request.user_reason = decision.reason
    await db.commit()

    # Trust tracking
    trust_service = TrustService(db)
    if decision.approved:
        await trust_service.record_action(str(current_user.id), request.agent_type, request.action, success=True)
    else:
        await trust_service.record_violation(str(current_user.id), request.agent_type, request.action)
    await db.commit()

    return {"status": request.status.value, "approval_id": str(approval_id)}


@router.post("/email/config", response_model=EmailConfigResponse)
async def save_email_config(
    data: EmailConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.email import EmailService
    service = EmailService(db)
    config = await service.save_config(
        user_id=str(current_user.id),
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_user=data.smtp_user,
        smtp_password=data.smtp_password,
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        imap_user=data.imap_user,
        imap_password=data.imap_password,
    )
    await db.commit()
    return EmailConfigResponse.model_validate(config)


@router.get("/email/config", response_model=EmailConfigResponse | None)
async def get_email_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.email import EmailService
    service = EmailService(db)
    config = await service.get_config(str(current_user.id))
    if not config:
        return None
    return EmailConfigResponse.model_validate(config)
```

**Step 3: Register in router**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1 import agents

# Phase 11: Multi-Agent System routers
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_agent_api.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/agents.py backend/app/api/v1/router.py backend/tests/test_agent_api.py
git commit -m "feat(agents): add Agent API endpoints for trust, approvals, email config"
```

---

## Task 11: SSE Activity Feed Endpoint

**Files:**
- Create: `backend/app/api/v1/agent_stream.py`
- Modify: `backend/app/api/v1/router.py`

**Step 1: Implement SSE endpoint**

Create `backend/app/api/v1/agent_stream.py`:

```python
"""SSE streaming endpoint for agent activity feed."""

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.agent_activity import AgentActivity
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agent Stream"])

# In-memory event queues per user (production: use Redis pub/sub)
_user_queues: dict[str, asyncio.Queue] = {}


def get_user_queue(user_id: str) -> asyncio.Queue:
    if user_id not in _user_queues:
        _user_queues[user_id] = asyncio.Queue(maxsize=100)
    return _user_queues[user_id]


async def publish_event(user_id: str, event_type: str, data: dict):
    """Publish an event to a user's SSE stream."""
    queue = get_user_queue(user_id)
    try:
        queue.put_nowait({"event": event_type, "data": data})
    except asyncio.QueueFull:
        logger.warning("SSE queue full for user %s, dropping event", user_id)


@router.get("/activity/stream")
async def agent_activity_stream(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """SSE stream of agent activity for the authenticated user."""
    user_id = str(current_user.id)
    queue = get_user_queue(user_id)

    async def event_generator():
        # Send initial heartbeat
        yield {"event": "connected", "data": json.dumps({"user_id": user_id})}

        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], default=str),
                }
            except asyncio.TimeoutError:
                # Send keepalive ping every 30s
                yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(event_generator())
```

**Step 2: Register route**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1 import agent_stream

router.include_router(agent_stream.router, prefix="/agents", tags=["Agent Stream"])
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/agent_stream.py backend/app/api/v1/router.py
git commit -m "feat(agents): add SSE activity stream endpoint"
```

---

## Task 12: Mobile API Services & Stores

**Files:**
- Create: `mobile/services/agents.ts`
- Create: `mobile/stores/agentStore.ts`
- Create: `mobile/stores/trustStore.ts`

**Step 1: Create agent API service**

Create `mobile/services/agents.ts`:

```typescript
import axios from "axios";
import { getApiUrl, getAuthHeaders } from "./api";

export interface TrustScore {
  agent_type: string;
  action_type: string;
  trust_level: number;
  successful_actions: number;
  total_actions: number;
}

export interface ApprovalRequest {
  id: string;
  agent_type: string;
  action: string;
  action_details: Record<string, any>;
  status: string;
  timeout_seconds: number;
  expires_at: string | null;
  created_at: string;
}

export interface EmailConfig {
  id: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  imap_host: string;
  imap_port: number;
  imap_user: string;
  is_active: boolean;
}

export interface AgentActivity {
  id: string;
  agent_type: string;
  action: string;
  status: string;
  details: Record<string, any> | null;
  result: string | null;
  duration_ms: number | null;
  error: string | null;
  created_at: string;
}

export const agentApi = {
  getTrustScores: async () => {
    const res = await axios.get(`${getApiUrl()}/agents/trust`, { headers: await getAuthHeaders() });
    return res.data;
  },
  setTrustLevel: async (agent_type: string, trust_level: number) => {
    const res = await axios.put(`${getApiUrl()}/agents/trust`, { agent_type, trust_level }, { headers: await getAuthHeaders() });
    return res.data;
  },
  getPendingApprovals: async () => {
    const res = await axios.get(`${getApiUrl()}/agents/approvals/pending`, { headers: await getAuthHeaders() });
    return res.data;
  },
  approve: async (approvalId: string, approved: boolean, reason?: string) => {
    const res = await axios.post(`${getApiUrl()}/agents/approve/${approvalId}`, { approved, reason }, { headers: await getAuthHeaders() });
    return res.data;
  },
  getEmailConfig: async () => {
    const res = await axios.get(`${getApiUrl()}/agents/email/config`, { headers: await getAuthHeaders() });
    return res.data;
  },
  saveEmailConfig: async (config: any) => {
    const res = await axios.post(`${getApiUrl()}/agents/email/config`, config, { headers: await getAuthHeaders() });
    return res.data;
  },
};
```

**Step 2: Create stores**

Create `mobile/stores/agentStore.ts`:

```typescript
import { create } from "zustand";
import { agentApi, ApprovalRequest } from "../services/agents";

interface AgentState {
  pendingApprovals: ApprovalRequest[];
  isLoading: boolean;
  fetchPendingApprovals: () => Promise<void>;
  approveAction: (id: string, approved: boolean, reason?: string) => Promise<void>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  pendingApprovals: [],
  isLoading: false,
  fetchPendingApprovals: async () => {
    set({ isLoading: true });
    try {
      const data = await agentApi.getPendingApprovals();
      set({ pendingApprovals: data });
    } catch (e) {
      console.error("Failed to fetch approvals:", e);
    } finally {
      set({ isLoading: false });
    }
  },
  approveAction: async (id, approved, reason) => {
    await agentApi.approve(id, approved, reason);
    await get().fetchPendingApprovals();
  },
}));
```

Create `mobile/stores/trustStore.ts`:

```typescript
import { create } from "zustand";
import { agentApi, TrustScore } from "../services/agents";

interface TrustState {
  scores: TrustScore[];
  fetchScores: () => Promise<void>;
  setLevel: (agentType: string, level: number) => Promise<void>;
}

export const useTrustStore = create<TrustState>((set) => ({
  scores: [],
  fetchScores: async () => {
    try {
      const data = await agentApi.getTrustScores();
      set({ scores: data.scores });
    } catch (e) {
      console.error("Failed to fetch trust scores:", e);
    }
  },
  setLevel: async (agentType, level) => {
    await agentApi.setTrustLevel(agentType, level);
    const data = await agentApi.getTrustScores();
    set({ scores: data.scores });
  },
}));
```

**Step 3: Commit**

```bash
git add mobile/services/agents.ts mobile/stores/agentStore.ts mobile/stores/trustStore.ts
git commit -m "feat(mobile): add agent API services and stores for trust and approvals"
```

---

## Task 13: Feature Flag Integration in ChatService

**Files:**
- Modify: `backend/app/services/chat.py` (add feature flag routing)
- Modify: `backend/app/api/v1/chat.py` (route based on flag)

**Step 1: Add agent chat method to ChatService**

Add to `backend/app/services/chat.py` a new method that routes to LangGraph when the feature flag is enabled. Add at the end of the ChatService class:

```python
    async def get_ai_response_langgraph(
        self, user_id: UUID, messages: list[dict], system_prompt: str
    ) -> str:
        """Get AI response via LangGraph supervisor (feature-flagged)."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        from app.agents.supervisor import create_agent

        # Convert messages to LangChain format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
                lc_messages.append(HumanMessage(content=content))
            elif msg["role"] == "assistant":
                content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
                lc_messages.append(AIMessage(content=content))

        agent = create_agent()
        state = {
            "messages": lc_messages,
            "user_id": str(user_id),
            "next_agent": None,
            "agent_plan": [],
            "trust_level": 1,
            "requires_approval": False,
            "pending_action": None,
            "agent_results": [],
            "current_agent": None,
            "error": None,
            "memory_context": None,
            "user_preferences": {},
            "system_prompt": system_prompt,
        }

        config = {"configurable": {"thread_id": f"user_{user_id}"}}
        result = await agent.ainvoke(state, config=config)

        # Extract final response
        if result.get("messages"):
            last = result["messages"][-1]
            return last.content if hasattr(last, "content") else str(last)
        return "Keine Antwort vom Agent-System."
```

**Step 2: Commit**

```bash
git add backend/app/services/chat.py
git commit -m "feat(agents): add LangGraph routing method to ChatService with feature flag"
```

---

## Task 14: Full Test Suite Run

**Files:** None (verification only)

**Step 1: Run all agent-related tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_agent_models.py tests/test_trust_service.py tests/test_agent_supervisor.py tests/test_email_service.py tests/test_research_service.py tests/test_agent_api.py -v`
Expected: All tests PASS

**Step 2: Run full backend test suite**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/ -v --ignore=tests/test_graphiti_client.py`
Expected: All tests PASS (excluding pre-existing graphiti issues)

**Step 3: TypeScript compilation check**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/mobile && npx tsc --noEmit`
Expected: No errors

---

## Task 15: Update Design Doc Milestone Checklist

**Files:**
- Modify: `docs/plans/2026-02-14-alice-agent-one-transformation-design.md`

**Step 1: Mark Milestone 6 items as complete**

Update the Milestone 6 checklist in the design doc, marking completed items with [x].

**Step 2: Commit**

```bash
git add docs/plans/
git commit -m "docs: update Milestone 6 checklist in design document"
```
