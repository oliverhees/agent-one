# Phase 10: Essential Integrations — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Google Calendar OAuth integration, Smart Reminders, bidirectional Webhooks with HMAC security, and n8n Bridge for workflow automation.

**Architecture:** Backend-First Monolith — all integrations within existing FastAPI backend. OAuth tokens encrypted in UserSettings JSONB via existing encrypt_value()/decrypt_value(). New models for CalendarEvent, Reminder, WebhookConfig, WebhookLog, N8nWorkflow. New scheduler steps for calendar sync and reminder processing. Mobile gets new API services, Zustand stores, and integration settings UI.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, httpx, cryptography (Fernet), Expo SDK 52, TypeScript, Zustand

---

### Task 1: DB Models (CalendarEvent, Reminder, WebhookConfig, WebhookLog, N8nWorkflow)

**Files:**
- Create: `backend/app/models/calendar_event.py`
- Create: `backend/app/models/reminder.py`
- Create: `backend/app/models/webhook.py`
- Create: `backend/app/models/n8n_workflow.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py` (add relationships)
- Test: `backend/tests/test_integration_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_integration_models.py
"""Tests for Phase 10 integration models."""
import pytest
from app.models.calendar_event import CalendarEvent
from app.models.reminder import Reminder, ReminderSource, ReminderStatus, ReminderRecurrence
from app.models.webhook import WebhookConfig, WebhookLog, WebhookDirection
from app.models.n8n_workflow import N8nWorkflow


class TestCalendarEventModel:
    def test_tablename(self):
        assert CalendarEvent.__tablename__ == "calendar_events"


class TestReminderModel:
    def test_reminder_source_enum(self):
        assert ReminderSource.MANUAL == "manual"
        assert ReminderSource.CHAT == "chat"
        assert ReminderSource.CALENDAR == "calendar"

    def test_reminder_status_enum(self):
        assert ReminderStatus.PENDING == "pending"
        assert ReminderStatus.SENT == "sent"
        assert ReminderStatus.DISMISSED == "dismissed"
        assert ReminderStatus.SNOOZED == "snoozed"

    def test_reminder_recurrence_enum(self):
        assert ReminderRecurrence.DAILY == "daily"
        assert ReminderRecurrence.WEEKLY == "weekly"
        assert ReminderRecurrence.MONTHLY == "monthly"


class TestWebhookModels:
    def test_webhook_direction_enum(self):
        assert WebhookDirection.INCOMING == "incoming"
        assert WebhookDirection.OUTGOING == "outgoing"

    def test_webhook_config_tablename(self):
        assert WebhookConfig.__tablename__ == "webhook_configs"

    def test_webhook_log_tablename(self):
        assert WebhookLog.__tablename__ == "webhook_logs"


class TestN8nWorkflowModel:
    def test_tablename(self):
        assert N8nWorkflow.__tablename__ == "n8n_workflows"
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_models.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement CalendarEvent model**

```python
# backend/app/models/calendar_event.py
"""CalendarEvent model for cached calendar data."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class CalendarEvent(BaseModel):
    """Cached calendar event from external provider."""

    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("ix_calendar_events_user_start", "user_id", "start_time"),
        Index("ix_calendar_events_external", "user_id", "external_id", unique=True),
        {"comment": "Cached calendar events from external providers"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this event",
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="External event ID (e.g. Google Event ID)",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Event title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Event description",
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Event start time (UTC)",
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Event end time (UTC)",
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Event location",
    )

    is_all_day: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is an all-day event",
    )

    calendar_provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="google",
        comment="Calendar provider: google",
    )

    raw_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Original event data from provider",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="calendar_events",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, title={self.title})>"
```

**Step 4: Implement Reminder model**

```python
# backend/app/models/reminder.py
"""Reminder model for smart reminders."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ReminderSource(str, enum.Enum):
    MANUAL = "manual"
    CHAT = "chat"
    CALENDAR = "calendar"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"


class ReminderRecurrence(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Reminder(BaseModel):
    """Smart reminder with multiple sources and recurrence."""

    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_user_status", "user_id", "status"),
        Index("ix_reminders_user_remind_at", "user_id", "remind_at"),
        {"comment": "Smart reminders from manual, chat, or calendar sources"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this reminder",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Reminder title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reminder description",
    )

    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When to send the reminder (UTC)",
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReminderSource.MANUAL,
        comment="Source: manual, chat, calendar",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReminderStatus.PENDING,
        comment="Status: pending, sent, dismissed, snoozed",
    )

    recurrence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        comment="Recurrence: daily, weekly, monthly, or null",
    )

    recurrence_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="End date for recurring reminders",
    )

    linked_task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional linked task",
    )

    linked_event_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional linked calendar event",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="reminders",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, title={self.title}, status={self.status})>"
```

**Step 5: Implement Webhook models**

```python
# backend/app/models/webhook.py
"""Webhook models for incoming/outgoing integrations."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class WebhookDirection(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class WebhookConfig(BaseModel):
    """Webhook configuration for incoming/outgoing integrations."""

    __tablename__ = "webhook_configs"
    __table_args__ = (
        Index("ix_webhook_configs_user_active", "user_id", "is_active"),
        {"comment": "Webhook configurations for external integrations"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this webhook",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Webhook display name",
    )

    url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="Target URL for outgoing / display URL for incoming",
    )

    secret: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="HMAC secret (encrypted via Fernet)",
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Direction: incoming or outgoing",
    )

    events: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="List of event types (outgoing only)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether webhook is active",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="webhook_configs",
        lazy="selectin",
    )

    logs: Mapped[list["WebhookLog"]] = relationship(
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig(id={self.id}, name={self.name}, dir={self.direction})>"


class WebhookLog(BaseModel):
    """Log entry for webhook executions."""

    __tablename__ = "webhook_logs"
    __table_args__ = (
        Index("ix_webhook_logs_webhook_created", "webhook_id", "created_at"),
        {"comment": "Webhook execution logs"},
    )

    webhook_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Webhook this log belongs to",
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Direction: incoming or outgoing",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Event type that triggered this log",
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Request payload",
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP response status code",
    )

    response_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Response body (truncated to 1000 chars)",
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Attempt number (1-3)",
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether the webhook call succeeded",
    )

    # Relationships
    webhook: Mapped["WebhookConfig"] = relationship(
        back_populates="logs",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WebhookLog(id={self.id}, event={self.event_type}, success={self.success})>"
```

**Step 6: Implement N8nWorkflow model**

```python
# backend/app/models/n8n_workflow.py
"""N8nWorkflow model for registered n8n workflows."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class N8nWorkflow(BaseModel):
    """Registered n8n workflow callable as external tool."""

    __tablename__ = "n8n_workflows"
    __table_args__ = (
        Index("ix_n8n_workflows_user_active", "user_id", "is_active"),
        {"comment": "Registered n8n workflows as external tools"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this workflow",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Workflow display name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Workflow description",
    )

    webhook_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="n8n webhook trigger URL",
    )

    input_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Expected input parameters schema",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether workflow is active",
    )

    execution_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total execution count",
    )

    last_executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Last execution timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="n8n_workflows",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<N8nWorkflow(id={self.id}, name={self.name})>"
```

**Step 7: Update `backend/app/models/__init__.py`**

Add these imports at the end of the import block:
```python
from app.models.calendar_event import CalendarEvent
from app.models.reminder import Reminder, ReminderSource, ReminderStatus, ReminderRecurrence
from app.models.webhook import WebhookConfig, WebhookLog, WebhookDirection
from app.models.n8n_workflow import N8nWorkflow
```

Add to `__all__`:
```python
    "CalendarEvent",
    "Reminder",
    "ReminderSource",
    "ReminderStatus",
    "ReminderRecurrence",
    "WebhookConfig",
    "WebhookLog",
    "WebhookDirection",
    "N8nWorkflow",
```

**Step 8: Update `backend/app/models/user.py`**

Add TYPE_CHECKING imports:
```python
    from app.models.calendar_event import CalendarEvent
    from app.models.reminder import Reminder
    from app.models.webhook import WebhookConfig
    from app.models.n8n_workflow import N8nWorkflow
```

Add relationships to User class (after `predicted_patterns`):
```python
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    n8n_workflows: Mapped[list["N8nWorkflow"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

**Step 9: Run tests to verify they pass**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_models.py -v`
Expected: PASS (all 10 tests)

**Step 10: Commit**

```bash
git add backend/app/models/calendar_event.py backend/app/models/reminder.py backend/app/models/webhook.py backend/app/models/n8n_workflow.py backend/app/models/__init__.py backend/app/models/user.py backend/tests/test_integration_models.py
git commit -m "feat: Phase 10 DB models for calendar, reminders, webhooks, n8n"
```

---

### Task 2: Alembic Migration 008

**Files:**
- Create: `backend/alembic/versions/008_phase10_integrations.py`

**Step 1: Write migration**

```python
# backend/alembic/versions/008_phase10_integrations.py
"""Phase 10: calendar_events, reminders, webhook_configs, webhook_logs, n8n_workflows tables.

Revision ID: 008_phase10_integrations
Revises: 007_phase9_predicted_patterns
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008_phase10_integrations"
down_revision: Union[str, None] = "007_phase9_predicted_patterns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # calendar_events
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("is_all_day", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("calendar_provider", sa.String(30), nullable=False, server_default="google"),
        sa.Column("raw_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment="Cached calendar events from external providers",
    )
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])
    op.create_index("ix_calendar_events_user_start", "calendar_events", ["user_id", "start_time"])
    op.create_index("ix_calendar_events_external", "calendar_events", ["user_id", "external_id"], unique=True)

    # reminders
    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("recurrence", sa.String(20), nullable=True),
        sa.Column("recurrence_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment="Smart reminders from manual, chat, or calendar sources",
    )
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"])
    op.create_index("ix_reminders_user_status", "reminders", ["user_id", "status"])
    op.create_index("ix_reminders_user_remind_at", "reminders", ["user_id", "remind_at"])

    # webhook_configs
    op.create_table(
        "webhook_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("secret", sa.String(500), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("events", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment="Webhook configurations for external integrations",
    )
    op.create_index("ix_webhook_configs_user_id", "webhook_configs", ["user_id"])
    op.create_index("ix_webhook_configs_user_active", "webhook_configs", ["user_id", "is_active"])

    # webhook_logs
    op.create_table(
        "webhook_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("attempt", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment="Webhook execution logs",
    )
    op.create_index("ix_webhook_logs_webhook_id", "webhook_logs", ["webhook_id"])
    op.create_index("ix_webhook_logs_webhook_created", "webhook_logs", ["webhook_id", "created_at"])

    # n8n_workflows
    op.create_table(
        "n8n_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("webhook_url", sa.String(2000), nullable=False),
        sa.Column("input_schema", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("execution_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment="Registered n8n workflows as external tools",
    )
    op.create_index("ix_n8n_workflows_user_id", "n8n_workflows", ["user_id"])
    op.create_index("ix_n8n_workflows_user_active", "n8n_workflows", ["user_id", "is_active"])


def downgrade() -> None:
    op.drop_table("n8n_workflows")
    op.drop_table("webhook_logs")
    op.drop_table("webhook_configs")
    op.drop_table("reminders")
    op.drop_table("calendar_events")
```

**Step 2: Run migration on test DB**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && DATABASE_URL=postgresql://alice:alice_dev_123@localhost:5434/alice_test alembic upgrade head`
Expected: OK

**Step 3: Commit**

```bash
git add backend/alembic/versions/008_phase10_integrations.py
git commit -m "db: Phase 10 migration for calendar, reminders, webhooks, n8n tables"
```

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/calendar.py`
- Create: `backend/app/schemas/reminder.py`
- Create: `backend/app/schemas/webhook.py`
- Create: `backend/app/schemas/n8n.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_integration_schemas.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_integration_schemas.py
"""Tests for Phase 10 Pydantic schemas."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.calendar import CalendarEventResponse, CalendarStatusResponse
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderSnoozeRequest
from app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookLogResponse
from app.schemas.n8n import N8nWorkflowCreate, N8nWorkflowResponse, N8nExecuteRequest


class TestCalendarSchemas:
    def test_calendar_event_response(self):
        data = CalendarEventResponse(
            id="test-id",
            title="Meeting",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            is_all_day=False,
            calendar_provider="google",
            created_at=datetime.now(timezone.utc),
        )
        assert data.title == "Meeting"

    def test_calendar_status(self):
        data = CalendarStatusResponse(connected=True, provider="google", last_synced=None)
        assert data.connected is True


class TestReminderSchemas:
    def test_reminder_create_minimal(self):
        data = ReminderCreate(
            title="Test",
            remind_at=datetime.now(timezone.utc),
        )
        assert data.source == "manual"

    def test_reminder_create_with_recurrence(self):
        data = ReminderCreate(
            title="Daily med",
            remind_at=datetime.now(timezone.utc),
            recurrence="daily",
        )
        assert data.recurrence == "daily"

    def test_reminder_create_invalid_recurrence(self):
        with pytest.raises(ValidationError):
            ReminderCreate(
                title="Bad",
                remind_at=datetime.now(timezone.utc),
                recurrence="every_two_days",
            )

    def test_snooze_request(self):
        data = ReminderSnoozeRequest(snooze_until=datetime.now(timezone.utc))
        assert data.snooze_until is not None


class TestWebhookSchemas:
    def test_webhook_create(self):
        data = WebhookCreate(
            name="Test Hook",
            url="https://example.com/hook",
            direction="outgoing",
            events=["task_completed"],
        )
        assert data.name == "Test Hook"

    def test_webhook_create_invalid_direction(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Bad",
                url="https://example.com",
                direction="bidirectional",
            )


class TestN8nSchemas:
    def test_workflow_create(self):
        data = N8nWorkflowCreate(
            name="CRM Lead",
            webhook_url="https://n8n.example.com/webhook/abc",
        )
        assert data.name == "CRM Lead"

    def test_execute_request(self):
        data = N8nExecuteRequest(input_data={"name": "Test"})
        assert data.input_data["name"] == "Test"
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_schemas.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement calendar schemas**

```python
# backend/app/schemas/calendar.py
"""Pydantic schemas for calendar endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CalendarEventResponse(BaseModel):
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
    events: list[CalendarEventResponse]
    total: int


class CalendarStatusResponse(BaseModel):
    connected: bool
    provider: str | None = None
    last_synced: datetime | None = None
```

**Step 4: Implement reminder schemas**

```python
# backend/app/schemas/reminder.py
"""Pydantic schemas for reminder endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str | None = None
    remind_at: datetime
    source: Literal["manual", "chat", "calendar"] = "manual"
    recurrence: Literal["daily", "weekly", "monthly"] | None = None
    recurrence_end: datetime | None = None
    linked_task_id: str | None = None
    linked_event_id: str | None = None


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    remind_at: datetime | None = None
    recurrence: Literal["daily", "weekly", "monthly"] | None = None
    recurrence_end: datetime | None = None


class ReminderResponse(BaseModel):
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
    reminders: list[ReminderResponse]
    total: int


class ReminderSnoozeRequest(BaseModel):
    snooze_until: datetime
```

**Step 5: Implement webhook schemas**

```python
# backend/app/schemas/webhook.py
"""Pydantic schemas for webhook endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    name: str = Field(max_length=200)
    url: str = Field(max_length=2000)
    direction: Literal["incoming", "outgoing"]
    events: list[str] = []


class WebhookUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2000)
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
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
    webhooks: list[WebhookResponse]
    total: int


class WebhookLogResponse(BaseModel):
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
    logs: list[WebhookLogResponse]
    total: int
```

**Step 6: Implement n8n schemas**

```python
# backend/app/schemas/n8n.py
"""Pydantic schemas for n8n Bridge endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class N8nWorkflowCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    webhook_url: str = Field(max_length=2000)
    input_schema: dict[str, Any] = {}


class N8nWorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    webhook_url: str | None = Field(default=None, max_length=2000)
    input_schema: dict[str, Any] | None = None
    is_active: bool | None = None


class N8nWorkflowResponse(BaseModel):
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
    workflows: list[N8nWorkflowResponse]
    total: int


class N8nExecuteRequest(BaseModel):
    input_data: dict[str, Any] = {}


class N8nExecuteResponse(BaseModel):
    workflow_id: str
    success: bool
    response_data: dict[str, Any] = {}
    execution_count: int
```

**Step 7: Update `backend/app/schemas/__init__.py`**

Add imports and __all__ entries for all new schemas.

**Step 8: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_schemas.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add backend/app/schemas/calendar.py backend/app/schemas/reminder.py backend/app/schemas/webhook.py backend/app/schemas/n8n.py backend/app/schemas/__init__.py backend/tests/test_integration_schemas.py
git commit -m "feat: Phase 10 Pydantic schemas for calendar, reminders, webhooks, n8n"
```

---

### Task 4: CalendarService

**Files:**
- Create: `backend/app/services/calendar.py`
- Modify: `backend/app/core/config.py` (add Google OAuth settings)
- Test: `backend/tests/test_calendar_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_calendar_service.py
"""Tests for CalendarService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.services.calendar import CalendarService


class TestCalendarService:
    @pytest.mark.asyncio
    async def test_get_today_events_empty(self, test_db):
        service = CalendarService(test_db)
        events = await service.get_today_events("00000000-0000-0000-0000-000000000000")
        assert events == []

    @pytest.mark.asyncio
    async def test_get_upcoming_events_empty(self, test_db):
        service = CalendarService(test_db)
        events = await service.get_upcoming_events("00000000-0000-0000-0000-000000000000")
        assert events == []

    @pytest.mark.asyncio
    async def test_disconnect_no_credentials(self, test_db):
        service = CalendarService(test_db)
        # Should not raise even if no credentials exist
        await service.disconnect("00000000-0000-0000-0000-000000000000")

    def test_build_google_auth_url(self):
        url = CalendarService.build_google_auth_url("http://localhost/callback", "test-state")
        assert "accounts.google.com" in url
        assert "test-state" in url
```

**Step 2: Implement CalendarService**

```python
# backend/app/services/calendar.py
"""Calendar integration service for Google Calendar."""

import logging
from datetime import datetime, timedelta, timezone, date, time
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.encryption import encrypt_value, decrypt_value
from app.models.calendar_event import CalendarEvent
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from sqlalchemy.orm import attributes

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events"


class CalendarService:
    """Service for Google Calendar integration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def build_google_auth_url(redirect_uri: str, state: str) -> str:
        """Build Google OAuth 2.0 authorization URL."""
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, user_id: str, code: str, redirect_uri: str) -> bool:
        """Exchange authorization code for tokens and store them."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code != 200:
                logger.error("Google token exchange failed: %s", response.text)
                return False

            tokens = response.json()

        await self._store_credentials(
            user_id,
            {
                "access_token": encrypt_value(tokens["access_token"]),
                "refresh_token": encrypt_value(tokens.get("refresh_token", "")),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
                ).isoformat(),
            },
        )
        return True

    async def disconnect(self, user_id: str) -> None:
        """Remove calendar credentials and cached events."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if user_settings:
            current = {**DEFAULT_SETTINGS, **user_settings.settings}
            current.pop("calendar_credentials", None)
            user_settings.settings = current
            attributes.flag_modified(user_settings, "settings")

        await self.db.execute(
            delete(CalendarEvent).where(CalendarEvent.user_id == UUID(user_id))
        )
        await self.db.flush()

    async def sync_events(self, user_id: str) -> list[dict]:
        """Sync events from Google Calendar to local cache."""
        access_token = await self._get_valid_access_token(user_id)
        if not access_token:
            return []

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=14)).isoformat()

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": "100",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                logger.error("Google Calendar API error: %s", response.text)
                return []

            data = response.json()

        events = data.get("items", [])
        result = []
        uid = UUID(user_id)

        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            is_all_day = "date" in start

            if is_all_day:
                start_dt = datetime.combine(date.fromisoformat(start["date"]), time.min, tzinfo=timezone.utc)
                end_dt = datetime.combine(date.fromisoformat(end["date"]), time.min, tzinfo=timezone.utc)
            else:
                start_dt = datetime.fromisoformat(start.get("dateTime", now.isoformat()))
                end_dt = datetime.fromisoformat(end.get("dateTime", now.isoformat()))

            stmt = pg_insert(CalendarEvent).values(
                user_id=uid,
                external_id=event["id"],
                title=event.get("summary", "(Kein Titel)"),
                description=event.get("description"),
                start_time=start_dt,
                end_time=end_dt,
                location=event.get("location"),
                is_all_day=is_all_day,
                calendar_provider="google",
                raw_data=event,
            ).on_conflict_do_update(
                index_elements=["user_id", "external_id"],
                set_={
                    "title": event.get("summary", "(Kein Titel)"),
                    "description": event.get("description"),
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "location": event.get("location"),
                    "is_all_day": is_all_day,
                    "raw_data": event,
                },
            )
            await self.db.execute(stmt)
            result.append({"id": event["id"], "title": event.get("summary", "")})

        await self.db.flush()
        return result

    async def get_today_events(self, user_id: str) -> list[dict]:
        """Get today's events from cache."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == UUID(user_id),
                CalendarEvent.start_time >= today_start,
                CalendarEvent.start_time < today_end,
            )
            .order_by(CalendarEvent.start_time)
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "id": str(e.id),
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "location": e.location,
                "is_all_day": e.is_all_day,
            }
            for e in events
        ]

    async def get_upcoming_events(self, user_id: str, hours: int = 24) -> list[dict]:
        """Get upcoming events within the next N hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)

        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == UUID(user_id),
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= cutoff,
            )
            .order_by(CalendarEvent.start_time)
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "id": str(e.id),
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "location": e.location,
                "is_all_day": e.is_all_day,
            }
            for e in events
        ]

    async def get_connection_status(self, user_id: str) -> dict:
        """Check if calendar is connected."""
        creds = await self._get_credentials(user_id)
        return {
            "connected": creds is not None,
            "provider": "google" if creds else None,
            "last_synced": None,
        }

    async def _store_credentials(self, user_id: str, credentials: dict) -> None:
        """Store encrypted credentials in UserSettings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if not user_settings:
            user_settings = UserSettings(user_id=UUID(user_id), settings=dict(DEFAULT_SETTINGS))
            self.db.add(user_settings)
            await self.db.flush()

        current = {**DEFAULT_SETTINGS, **user_settings.settings}
        current["calendar_credentials"] = credentials
        user_settings.settings = current
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

    async def _get_credentials(self, user_id: str) -> dict | None:
        """Get calendar credentials from UserSettings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if not user_settings:
            return None
        current = {**DEFAULT_SETTINGS, **user_settings.settings}
        return current.get("calendar_credentials")

    async def _get_valid_access_token(self, user_id: str) -> str | None:
        """Get a valid access token, refreshing if needed."""
        creds = await self._get_credentials(user_id)
        if not creds:
            return None

        expires_at_str = creds.get("expires_at", "")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) < expires_at - timedelta(minutes=5):
                return decrypt_value(creds["access_token"])

        # Refresh token
        refresh_token = decrypt_value(creds.get("refresh_token", ""))
        if not refresh_token:
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            if response.status_code != 200:
                logger.error("Google token refresh failed: %s", response.text)
                return None

            tokens = response.json()

        new_creds = {
            "access_token": encrypt_value(tokens["access_token"]),
            "refresh_token": creds["refresh_token"],
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
            ).isoformat(),
        }
        await self._store_credentials(user_id, new_creds)
        return tokens["access_token"]
```

**Step 3: Add Google config to `backend/app/core/config.py`**

Add after `openai_api_key`:
```python
    # Google Calendar OAuth
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="http://localhost:8000/api/v1/calendar/auth/google/callback", alias="GOOGLE_REDIRECT_URI")
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_calendar_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/calendar.py backend/app/core/config.py backend/tests/test_calendar_service.py
git commit -m "feat: CalendarService with Google OAuth and event sync"
```

---

### Task 5: WebhookService + N8nBridgeService

**Files:**
- Create: `backend/app/services/webhook.py`
- Create: `backend/app/services/n8n_bridge.py`
- Test: `backend/tests/test_webhook_service.py`
- Test: `backend/tests/test_n8n_service.py`

**Step 1: Write webhook test**

```python
# backend/tests/test_webhook_service.py
"""Tests for WebhookService."""
import pytest
import hashlib
import hmac
import json
from app.services.webhook import WebhookService


class TestWebhookService:
    def test_generate_secret(self):
        secret = WebhookService.generate_secret()
        assert len(secret) == 64  # 32 bytes hex

    def test_verify_signature_valid(self):
        secret = "test-secret"
        payload = json.dumps({"event": "test"}).encode()
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected}"
        assert WebhookService.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        assert WebhookService.verify_signature(b"data", "sha256=bad", "secret") is False
```

**Step 2: Implement WebhookService**

```python
# backend/app/services/webhook.py
"""Webhook service for incoming/outgoing webhook management."""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_value, decrypt_value
from app.models.webhook import WebhookConfig, WebhookLog

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF = [1, 4, 16]  # seconds


class WebhookService:
    """Service for managing and executing webhooks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_secret() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature[7:], expected)

    @staticmethod
    def compute_signature(payload: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    async def create_webhook(self, user_id: str, name: str, url: str, direction: str, events: list[str] | None = None) -> WebhookConfig:
        secret = self.generate_secret()
        webhook = WebhookConfig(
            user_id=UUID(user_id),
            name=name,
            url=url,
            secret=encrypt_value(secret),
            direction=direction,
            events=events or [],
            is_active=True,
        )
        self.db.add(webhook)
        await self.db.flush()
        await self.db.refresh(webhook)
        return webhook

    async def list_webhooks(self, user_id: str) -> tuple[list[WebhookConfig], int]:
        count_stmt = select(func.count()).select_from(WebhookConfig).where(WebhookConfig.user_id == UUID(user_id))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(WebhookConfig).where(WebhookConfig.user_id == UUID(user_id)).order_by(WebhookConfig.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_webhook(self, user_id: str, webhook_id: str) -> WebhookConfig | None:
        stmt = select(WebhookConfig).where(WebhookConfig.id == UUID(webhook_id), WebhookConfig.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_webhook(self, user_id: str, webhook_id: str) -> bool:
        webhook = await self.get_webhook(user_id, webhook_id)
        if not webhook:
            return False
        await self.db.delete(webhook)
        await self.db.flush()
        return True

    async def process_incoming(self, webhook_id: str, payload: dict, signature: str) -> dict:
        """Process an incoming webhook request."""
        stmt = select(WebhookConfig).where(WebhookConfig.id == UUID(webhook_id), WebhookConfig.is_active == True)
        result = await self.db.execute(stmt)
        webhook = result.scalar_one_or_none()

        if not webhook:
            return {"error": "Webhook not found or inactive", "status": 404}

        secret = decrypt_value(webhook.secret)
        payload_bytes = json.dumps(payload).encode()

        if not self.verify_signature(payload_bytes, signature, secret):
            log = WebhookLog(
                webhook_id=webhook.id, direction="incoming",
                event_type=payload.get("event", "unknown"),
                payload=payload, success=False, attempt=1,
            )
            self.db.add(log)
            await self.db.flush()
            return {"error": "Invalid signature", "status": 401}

        log = WebhookLog(
            webhook_id=webhook.id, direction="incoming",
            event_type=payload.get("event", "unknown"),
            payload=payload, success=True, status_code=200, attempt=1,
        )
        self.db.add(log)
        await self.db.flush()

        return {"status": 200, "message": "Webhook received", "event": payload.get("event")}

    async def send_outgoing(self, event_type: str, event_data: dict, user_id: str) -> int:
        """Send outgoing webhook to all matching configs. Returns count of successful sends."""
        stmt = select(WebhookConfig).where(
            WebhookConfig.user_id == UUID(user_id),
            WebhookConfig.direction == "outgoing",
            WebhookConfig.is_active == True,
        )
        result = await self.db.execute(stmt)
        webhooks = result.scalars().all()

        success_count = 0
        for webhook in webhooks:
            events_list = webhook.events if isinstance(webhook.events, list) else []
            if event_type not in events_list:
                continue

            secret = decrypt_value(webhook.secret)
            payload = {"event": event_type, "data": event_data, "timestamp": datetime.now(timezone.utc).isoformat()}
            payload_bytes = json.dumps(payload).encode()
            signature = self.compute_signature(payload_bytes, secret)

            for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            webhook.url,
                            content=payload_bytes,
                            headers={
                                "Content-Type": "application/json",
                                "X-Webhook-Signature": signature,
                            },
                        )

                    log = WebhookLog(
                        webhook_id=webhook.id, direction="outgoing",
                        event_type=event_type, payload=payload,
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else None,
                        attempt=attempt, success=response.is_success,
                    )
                    self.db.add(log)

                    if response.is_success:
                        success_count += 1
                        break
                except Exception as e:
                    log = WebhookLog(
                        webhook_id=webhook.id, direction="outgoing",
                        event_type=event_type, payload=payload,
                        response_body=str(e)[:1000],
                        attempt=attempt, success=False,
                    )
                    self.db.add(log)

            await self.db.flush()

        return success_count

    async def get_logs(self, user_id: str, webhook_id: str, limit: int = 50) -> tuple[list[WebhookLog], int]:
        webhook = await self.get_webhook(user_id, webhook_id)
        if not webhook:
            return [], 0

        count_stmt = select(func.count()).select_from(WebhookLog).where(WebhookLog.webhook_id == webhook.id)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(WebhookLog).where(WebhookLog.webhook_id == webhook.id).order_by(WebhookLog.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
```

**Step 3: Implement N8nBridgeService**

```python
# backend/app/services/n8n_bridge.py
"""n8n Bridge service for workflow registration and execution."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.n8n_workflow import N8nWorkflow

logger = logging.getLogger(__name__)


class N8nBridgeService:
    """Service for managing and executing n8n workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_workflow(self, user_id: str, name: str, webhook_url: str, description: str | None = None, input_schema: dict | None = None) -> N8nWorkflow:
        workflow = N8nWorkflow(
            user_id=UUID(user_id),
            name=name,
            description=description,
            webhook_url=webhook_url,
            input_schema=input_schema or {},
            is_active=True,
        )
        self.db.add(workflow)
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def list_workflows(self, user_id: str) -> tuple[list[N8nWorkflow], int]:
        count_stmt = select(func.count()).select_from(N8nWorkflow).where(N8nWorkflow.user_id == UUID(user_id))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(N8nWorkflow).where(N8nWorkflow.user_id == UUID(user_id)).order_by(N8nWorkflow.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_workflow(self, user_id: str, workflow_id: str) -> N8nWorkflow | None:
        stmt = select(N8nWorkflow).where(N8nWorkflow.id == UUID(workflow_id), N8nWorkflow.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def execute_workflow(self, user_id: str, workflow_id: str, input_data: dict[str, Any] | None = None) -> dict:
        workflow = await self.get_workflow(user_id, workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found"}

        if not workflow.is_active:
            return {"success": False, "error": "Workflow is inactive"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    workflow.webhook_url,
                    json=input_data or {},
                    headers={"Content-Type": "application/json"},
                )

            workflow.execution_count += 1
            workflow.last_executed_at = datetime.now(timezone.utc)
            await self.db.flush()

            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw": response.text[:1000]},
                "execution_count": workflow.execution_count,
            }
        except Exception as e:
            logger.error("n8n workflow execution failed: %s", e)
            workflow.execution_count += 1
            workflow.last_executed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return {"success": False, "error": str(e), "execution_count": workflow.execution_count}

    async def delete_workflow(self, user_id: str, workflow_id: str) -> bool:
        workflow = await self.get_workflow(user_id, workflow_id)
        if not workflow:
            return False
        await self.db.delete(workflow)
        await self.db.flush()
        return True
```

**Step 4: Write n8n test**

```python
# backend/tests/test_n8n_service.py
"""Tests for N8nBridgeService."""
import pytest
from app.services.n8n_bridge import N8nBridgeService


class TestN8nBridgeService:
    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, test_db):
        service = N8nBridgeService(test_db)
        workflows, total = await service.list_workflows("00000000-0000-0000-0000-000000000000")
        assert workflows == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(self, test_db):
        service = N8nBridgeService(test_db)
        result = await service.get_workflow("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000001")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_workflow(self, test_db):
        service = N8nBridgeService(test_db)
        result = await service.delete_workflow("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000001")
        assert result is False
```

**Step 5: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_webhook_service.py tests/test_n8n_service.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/webhook.py backend/app/services/n8n_bridge.py backend/tests/test_webhook_service.py backend/tests/test_n8n_service.py
git commit -m "feat: WebhookService with HMAC + N8nBridgeService"
```

---

### Task 6: API Endpoints (Calendar, Reminders, Webhooks, n8n)

**Files:**
- Create: `backend/app/api/v1/calendar.py`
- Create: `backend/app/api/v1/reminders.py`
- Create: `backend/app/api/v1/webhooks.py`
- Create: `backend/app/api/v1/n8n.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_integration_api.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_integration_api.py
"""Tests for Phase 10 integration API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestCalendarAPI:
    @pytest.mark.asyncio
    async def test_calendar_status_not_connected(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/calendar/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False

    @pytest.mark.asyncio
    async def test_calendar_events_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/calendar/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []

    @pytest.mark.asyncio
    async def test_calendar_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/calendar/status")
        assert response.status_code == 403


class TestReminderAPI:
    @pytest.mark.asyncio
    async def test_list_reminders_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/reminders")
        assert response.status_code == 200
        data = response.json()
        assert data["reminders"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_reminder(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/reminders",
            json={"title": "Test Reminder", "remind_at": "2026-12-31T10:00:00Z"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Reminder"
        assert data["source"] == "manual"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_reminder(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.delete(f"/api/v1/reminders/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reminders_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/reminders")
        assert response.status_code == 403


class TestWebhookAPI:
    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/webhooks")
        assert response.status_code == 200
        data = response.json()
        assert data["webhooks"] == []

    @pytest.mark.asyncio
    async def test_create_webhook(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/webhooks",
            json={"name": "Test", "url": "https://example.com/hook", "direction": "outgoing", "events": ["task_completed"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"
        assert data["direction"] == "outgoing"

    @pytest.mark.asyncio
    async def test_webhooks_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/webhooks")
        assert response.status_code == 403


class TestN8nAPI:
    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/n8n/workflows")
        assert response.status_code == 200
        data = response.json()
        assert data["workflows"] == []

    @pytest.mark.asyncio
    async def test_create_workflow(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/n8n/workflows",
            json={"name": "CRM Lead", "webhook_url": "https://n8n.example.com/webhook/abc"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "CRM Lead"

    @pytest.mark.asyncio
    async def test_n8n_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/n8n/workflows")
        assert response.status_code == 403


class TestRouterRegistration:
    def test_calendar_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/calendar" in p for p in paths)

    def test_reminders_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/reminders" in p for p in paths)

    def test_webhooks_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/webhooks" in p for p in paths)

    def test_n8n_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/n8n" in p for p in paths)
```

**Step 2: Implement calendar API**

```python
# backend/app/api/v1/calendar.py
"""Calendar API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.calendar import CalendarEventListResponse, CalendarEventResponse, CalendarStatusResponse
from app.services.calendar import CalendarService

router = APIRouter(tags=["Calendar"])


@router.get("/status", response_model=CalendarStatusResponse)
async def get_calendar_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    status = await service.get_connection_status(str(current_user.id))
    return CalendarStatusResponse(**status)


@router.get("/events", response_model=CalendarEventListResponse)
async def get_today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.get_today_events(str(current_user.id))
    return CalendarEventListResponse(events=events, total=len(events))


@router.get("/events/upcoming", response_model=CalendarEventListResponse)
async def get_upcoming_events(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.get_upcoming_events(str(current_user.id), hours=hours)
    return CalendarEventListResponse(events=events, total=len(events))


@router.post("/sync")
async def sync_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.sync_events(str(current_user.id))
    await db.commit()
    return {"synced_count": len(events)}


@router.delete("/disconnect")
async def disconnect_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    await service.disconnect(str(current_user.id))
    await db.commit()
    return {"message": "Calendar disconnected"}


@router.get("/auth/google")
async def google_auth_start(
    current_user: User = Depends(get_current_user),
):
    from app.core.config import settings
    url = CalendarService.build_google_auth_url(settings.google_redirect_uri, str(current_user.id))
    return {"auth_url": url}


@router.get("/auth/google/callback")
async def google_auth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    from app.core.config import settings
    service = CalendarService(db)
    success = await service.exchange_code(state, code, settings.google_redirect_uri)
    if not success:
        raise HTTPException(status_code=400, detail="OAuth token exchange failed")
    await db.commit()
    return {"message": "Calendar connected successfully"}
```

**Step 3: Implement reminders API**

```python
# backend/app/api/v1/reminders.py
"""Reminder API endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.reminder import Reminder, ReminderStatus
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate, ReminderListResponse, ReminderResponse,
    ReminderSnoozeRequest, ReminderUpdate,
)

router = APIRouter(tags=["Reminders"])


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count()).select_from(Reminder).where(Reminder.user_id == current_user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Reminder).where(Reminder.user_id == current_user.id).order_by(Reminder.remind_at)
    result = await db.execute(stmt)
    reminders = result.scalars().all()

    return ReminderListResponse(
        reminders=[ReminderResponse.model_validate(r) for r in reminders],
        total=total,
    )


@router.get("/upcoming", response_model=ReminderListResponse)
async def list_upcoming_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Reminder)
        .where(Reminder.user_id == current_user.id, Reminder.status == ReminderStatus.PENDING)
        .order_by(Reminder.remind_at)
    )
    result = await db.execute(stmt)
    reminders = result.scalars().all()

    return ReminderListResponse(
        reminders=[ReminderResponse.model_validate(r) for r in reminders],
        total=len(reminders),
    )


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    body: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = Reminder(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        remind_at=body.remind_at,
        source=body.source,
        recurrence=body.recurrence,
        recurrence_end=body.recurrence_end,
        linked_task_id=UUID(body.linked_task_id) if body.linked_task_id else None,
        linked_event_id=UUID(body.linked_event_id) if body.linked_event_id else None,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    body: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)

    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.delete(reminder)
    await db.commit()
    return {"message": "Reminder deleted"}


@router.post("/{reminder_id}/snooze", response_model=ReminderResponse)
async def snooze_reminder(
    reminder_id: UUID,
    body: ReminderSnoozeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.remind_at = body.snooze_until
    reminder.status = ReminderStatus.SNOOZED
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
async def dismiss_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.status = ReminderStatus.DISMISSED
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)
```

**Step 4: Implement webhooks API**

```python
# backend/app/api/v1/webhooks.py
"""Webhook API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate, WebhookListResponse, WebhookLogListResponse,
    WebhookLogResponse, WebhookResponse, WebhookUpdate,
)
from app.services.webhook import WebhookService

router = APIRouter(tags=["Webhooks"])


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    webhooks, total = await service.list_webhooks(str(current_user.id))
    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(w) for w in webhooks],
        total=total,
    )


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    webhook = await service.create_webhook(
        str(current_user.id), body.name, body.url, body.direction, body.events,
    )
    await db.commit()
    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    deleted = await service.delete_webhook(str(current_user.id), str(webhook_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()
    return {"message": "Webhook deleted"}


@router.get("/{webhook_id}/logs", response_model=WebhookLogListResponse)
async def get_webhook_logs(
    webhook_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    logs, total = await service.get_logs(str(current_user.id), str(webhook_id), limit)
    return WebhookLogListResponse(
        logs=[WebhookLogResponse.model_validate(l) for l in logs],
        total=total,
    )


@router.post("/incoming/{webhook_id}")
async def incoming_webhook(
    webhook_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for receiving incoming webhooks (no auth required)."""
    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.json()

    service = WebhookService(db)
    result = await service.process_incoming(str(webhook_id), body, signature)
    await db.commit()

    status = result.pop("status", 200)
    if status != 200:
        raise HTTPException(status_code=status, detail=result.get("error", "Error"))
    return result
```

**Step 5: Implement n8n API**

```python
# backend/app/api/v1/n8n.py
"""n8n Bridge API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.n8n import (
    N8nExecuteRequest, N8nExecuteResponse, N8nWorkflowCreate,
    N8nWorkflowListResponse, N8nWorkflowResponse, N8nWorkflowUpdate,
)
from app.services.n8n_bridge import N8nBridgeService

router = APIRouter(tags=["n8n"])


@router.get("/workflows", response_model=N8nWorkflowListResponse)
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    workflows, total = await service.list_workflows(str(current_user.id))
    return N8nWorkflowListResponse(
        workflows=[N8nWorkflowResponse.model_validate(w) for w in workflows],
        total=total,
    )


@router.post("/workflows", response_model=N8nWorkflowResponse, status_code=201)
async def create_workflow(
    body: N8nWorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    workflow = await service.register_workflow(
        str(current_user.id), body.name, body.webhook_url,
        body.description, body.input_schema,
    )
    await db.commit()
    return N8nWorkflowResponse.model_validate(workflow)


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    deleted = await service.delete_workflow(str(current_user.id), str(workflow_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.commit()
    return {"message": "Workflow deleted"}


@router.post("/workflows/{workflow_id}/execute", response_model=N8nExecuteResponse)
async def execute_workflow(
    workflow_id: UUID,
    body: N8nExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    result = await service.execute_workflow(str(current_user.id), str(workflow_id), body.input_data)
    await db.commit()

    if "error" in result and not result.get("success"):
        raise HTTPException(status_code=404, detail=result["error"])

    return N8nExecuteResponse(
        workflow_id=str(workflow_id),
        success=result.get("success", False),
        response_data=result.get("response_data", {}),
        execution_count=result.get("execution_count", 0),
    )
```

**Step 6: Update router**

Add to `backend/app/api/v1/router.py` imports:
```python
from app.api.v1 import calendar, reminders, webhooks, n8n
```

Add after prediction router:
```python
# Phase 10: Essential Integrations routers
router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(n8n.router, prefix="/n8n", tags=["n8n"])
```

**Step 7: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_api.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add backend/app/api/v1/calendar.py backend/app/api/v1/reminders.py backend/app/api/v1/webhooks.py backend/app/api/v1/n8n.py backend/app/api/v1/router.py backend/tests/test_integration_api.py
git commit -m "feat: Phase 10 API endpoints for calendar, reminders, webhooks, n8n"
```

---

### Task 7: Scheduler Integration (Calendar Sync + Reminders)

**Files:**
- Modify: `backend/app/services/scheduler.py`
- Test: `backend/tests/test_integration_scheduler.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_integration_scheduler.py
"""Tests for Phase 10 scheduler integration."""
import pytest
from unittest.mock import patch, AsyncMock


class TestCalendarSyncScheduler:
    @pytest.mark.asyncio
    async def test_calendar_sync_skipped_without_integrations_module(self):
        from app.services.scheduler import _process_calendar_sync
        settings = {"active_modules": ["core", "adhs"]}
        await _process_calendar_sync("00000000-0000-0000-0000-000000000000", settings)
        # No error, just skipped

    @pytest.mark.asyncio
    async def test_calendar_sync_skipped_without_credentials(self):
        from app.services.scheduler import _process_calendar_sync
        settings = {"active_modules": ["core", "integrations"]}
        await _process_calendar_sync("00000000-0000-0000-0000-000000000000", settings)


class TestReminderScheduler:
    @pytest.mark.asyncio
    async def test_reminders_skipped_without_integrations_module(self):
        from app.services.scheduler import _process_reminders
        settings = {"active_modules": ["core", "adhs"]}
        await _process_reminders("00000000-0000-0000-0000-000000000000", settings)
```

**Step 2: Add scheduler functions**

Add to `backend/app/services/scheduler.py` after `_process_predictions()`:

```python
    # 7. Calendar sync (if integrations module active)
    try:
        await _process_calendar_sync(user_id, settings)
    except Exception:
        logger.exception("Calendar sync error for user %s", user_id)

    # 8. Reminder processing (if integrations module active)
    try:
        await _process_reminders(user_id, settings)
    except Exception:
        logger.exception("Reminder processing error for user %s", user_id)
```

Add these new functions:

```python
async def _process_calendar_sync(user_id: UUID, settings: dict) -> None:
    """Sync calendar events if integrations module is active."""
    active_modules = settings.get("active_modules", ["core", "adhs"])
    if "integrations" not in active_modules:
        return

    # Only sync every 30 minutes (6 ticks)
    if not hasattr(_process_calendar_sync, "_tick_count"):
        _process_calendar_sync._tick_count = {}
    count = _process_calendar_sync._tick_count.get(str(user_id), 0)
    _process_calendar_sync._tick_count[str(user_id)] = count + 1
    if count % 6 != 0:
        return

    async with AsyncSessionLocal() as db:
        from app.services.calendar import CalendarService
        service = CalendarService(db)
        status = await service.get_connection_status(str(user_id))
        if not status["connected"]:
            return
        events = await service.sync_events(str(user_id))
        await db.commit()
        if events:
            logger.info("Calendar sync: %d events for user %s", len(events), user_id)


async def _process_reminders(user_id: UUID, settings: dict) -> None:
    """Process pending reminders and send push notifications."""
    active_modules = settings.get("active_modules", ["core", "adhs"])
    if "integrations" not in active_modules:
        return

    from app.models.reminder import Reminder, ReminderStatus, ReminderRecurrence
    from datetime import datetime, timezone, timedelta

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        stmt = select(Reminder).where(
            Reminder.user_id == user_id,
            Reminder.status == ReminderStatus.PENDING,
            Reminder.remind_at <= now,
        )
        result = await db.execute(stmt)
        due_reminders = result.scalars().all()

        token = settings.get("expo_push_token")

        for reminder in due_reminders:
            if token:
                await NotificationService.send_notification(
                    PushNotification(
                        to=token,
                        title="Erinnerung",
                        body=reminder.title,
                        data={"type": "reminder", "id": str(reminder.id)},
                    )
                )

            reminder.status = ReminderStatus.SENT

            # Create next occurrence for recurring reminders
            if reminder.recurrence:
                next_at = _calculate_next_occurrence(reminder.remind_at, reminder.recurrence)
                if reminder.recurrence_end is None or next_at <= reminder.recurrence_end:
                    new_reminder = Reminder(
                        user_id=reminder.user_id,
                        title=reminder.title,
                        description=reminder.description,
                        remind_at=next_at,
                        source=reminder.source,
                        recurrence=reminder.recurrence,
                        recurrence_end=reminder.recurrence_end,
                        linked_task_id=reminder.linked_task_id,
                    )
                    db.add(new_reminder)

        await db.commit()


def _calculate_next_occurrence(current: datetime, recurrence: str) -> datetime:
    """Calculate the next occurrence for a recurring reminder."""
    if recurrence == "daily":
        return current + timedelta(days=1)
    elif recurrence == "weekly":
        return current + timedelta(weeks=1)
    elif recurrence == "monthly":
        return current + timedelta(days=30)
    return current + timedelta(days=1)
```

Also add `"integrations"` module to `backend/app/core/modules.py`:

```python
    "integrations": {
        "label": "Integrationen",
        "icon": "link-outline",
        "description": "Google Calendar, Smart Reminders, Webhooks und n8n Workflows",
        "default_config": {
            "calendar_sync_enabled": True,
            "reminder_notifications": True,
        },
    },
```

**Step 3: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_scheduler.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/scheduler.py backend/app/core/modules.py backend/tests/test_integration_scheduler.py
git commit -m "feat: Scheduler steps for calendar sync and reminder processing"
```

---

### Task 8: Mobile API Services + Zustand Stores

**Files:**
- Create: `mobile/services/calendar.ts`
- Create: `mobile/services/reminders.ts`
- Create: `mobile/services/webhooks.ts`
- Create: `mobile/services/n8n.ts`
- Create: `mobile/stores/calendarStore.ts`
- Create: `mobile/stores/reminderStore.ts`
- Create: `mobile/stores/webhookStore.ts`
- Create: `mobile/stores/n8nStore.ts`

**Step 1: Create API services**

Follow the pattern from `mobile/services/predictions.ts`. Each service exports typed interfaces and an API object using the base `api` client.

Key interfaces:
- `CalendarEvent`, `CalendarStatus`, `calendarApi`
- `Reminder`, `ReminderCreate`, `remindersApi`
- `Webhook`, `WebhookCreate`, `webhooksApi`
- `N8nWorkflow`, `N8nWorkflowCreate`, `n8nApi`

**Step 2: Create Zustand stores**

Follow the pattern from `mobile/stores/predictionStore.ts`. Each store has:
- State arrays (items, isLoading, error)
- Async actions (fetch, create, delete)
- Optimistic updates where appropriate

**Step 3: Commit**

```bash
git add mobile/services/calendar.ts mobile/services/reminders.ts mobile/services/webhooks.ts mobile/services/n8n.ts mobile/stores/calendarStore.ts mobile/stores/reminderStore.ts mobile/stores/webhookStore.ts mobile/stores/n8nStore.ts
git commit -m "feat: Mobile API services and Zustand stores for Phase 10"
```

---

### Task 9: Mobile Screens (Settings Integration + Calendar Tab)

**Files:**
- Create: `mobile/app/(tabs)/settings/integrations.tsx`
- Create: `mobile/app/(tabs)/calendar/_layout.tsx`
- Create: `mobile/app/(tabs)/calendar/index.tsx`
- Modify: `mobile/app/(tabs)/_layout.tsx` (add calendar tab)

**Step 1: Create Settings > Integrations screen**

Integration settings with:
- Google Calendar connect/disconnect toggle
- Webhook list with add button
- n8n workflow list with add button

**Step 2: Create Calendar tab screen**

Calendar tab showing:
- Today's events as cards
- Pull-to-refresh for manual sync
- Connection prompt if not connected

**Step 3: Update tab layout**

Add to `TAB_CONFIG` in `_layout.tsx`:
```typescript
{
  name: "calendar",
  title: "Kalender",
  icon: "calendar-outline",
  requiredModules: ["integrations"],
},
```

**Step 4: Commit**

```bash
git add mobile/app/(tabs)/settings/integrations.tsx mobile/app/(tabs)/calendar/_layout.tsx mobile/app/(tabs)/calendar/index.tsx mobile/app/(tabs)/_layout.tsx
git commit -m "feat: Mobile integration settings and calendar tab screens"
```

---

### Task 10: Full Test Suite Run

**Files:**
- None (validation only)

**Step 1: Run all Phase 10 backend tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_integration_models.py tests/test_integration_schemas.py tests/test_calendar_service.py tests/test_webhook_service.py tests/test_n8n_service.py tests/test_integration_api.py tests/test_integration_scheduler.py -v`
Expected: ALL PASS

**Step 2: Run full backend test suite**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/ -v --timeout=60 2>&1 | tail -30`
Expected: All Phase 10 tests pass. Pre-existing failures in nudge/voice tests are expected (not regressions).

**Step 3: Verify TypeScript compilation**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/mobile && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors from Phase 10 files.

**Step 4: Commit**

No commit needed (validation only).

---

### Task 11: Update Milestone 5 Checklist

**Files:**
- Modify: `docs/plans/2026-02-14-alice-agent-one-transformation-design.md`

Update Milestone 5 checklist items to `[x]`:
```markdown
### Milestone 5: Essential Integrations
- [x] Google Calendar OAuth 2.0 Integration (Read/Write)
- [ ] Apple Calendar Integration (EventKit via Expo) — deferred
- [x] Calendar-Daten in Morning Briefing einbinden
- [x] Termin-Erinnerungen via Push
- [x] Smart Reminder System (zeit-/kontextbasiert)
- [x] Wiederkehrende Erinnerungen
- [x] Push Notification Queue mit Priority
- [x] Incoming Webhooks Endpoint
- [x] Outgoing Webhooks System
- [x] n8n Bridge Foundation (Workflow -> MCP Tool)
```

**Commit:**

```bash
git add docs/plans/2026-02-14-alice-agent-one-transformation-design.md
git commit -m "docs: Phase 10 Milestone 5 checklist updated"
```
