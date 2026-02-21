# Phase 8: Morning Briefing & Adaptive Planning — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a daily Morning Briefing system that generates personalized, ADHS-optimized daily plans with LLM-powered summaries, energy-based task prioritization, and a Brain Dump capture feature.

**Architecture:** The BriefingService aggregates data from WellbeingService, PatternAnalyzer, and Task queries to generate a structured daily briefing. An LLM call creates a personalized German-language summary. The scheduler triggers briefing generation at the user's configured `briefing_time`. A new Expo tab displays the briefing with swipeable task cards and a brain dump input.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Anthropic Claude API (httpx), Expo SDK 52, TypeScript, Zustand

**Linear Epics:**
- HR-459 (parent project: ALICE)
- New epics to create: Briefing Engine, Expo Briefing UI

---

## Task 1: Briefing DB Model

**Files:**
- Create: `backend/app/models/briefing.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py` (add relationship)
- Test: `backend/tests/test_briefing_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_briefing_models.py
"""Tests for Briefing DB model."""

import pytest
from datetime import datetime, timezone


class TestBriefingModelImport:
    def test_briefing_model_importable(self):
        from app.models.briefing import Briefing
        assert Briefing is not None

    def test_briefing_status_enum(self):
        from app.models.briefing import BriefingStatus
        assert BriefingStatus.GENERATED == "generated"
        assert BriefingStatus.DELIVERED == "delivered"
        assert BriefingStatus.READ == "read"

    def test_briefing_has_tablename(self):
        from app.models.briefing import Briefing
        assert Briefing.__tablename__ == "briefings"

    def test_briefing_in_models_init(self):
        from app.models import Briefing
        assert Briefing is not None


class TestBriefingModelFields:
    def test_has_user_id_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "user_id")

    def test_has_date_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "briefing_date")

    def test_has_content_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "content")

    def test_has_tasks_suggested_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "tasks_suggested")

    def test_has_wellbeing_snapshot_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "wellbeing_snapshot")

    def test_has_status_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "status")

    def test_has_read_at_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "read_at")


@pytest.mark.asyncio
class TestBriefingCRUD:
    async def test_create_briefing(self, test_db, test_user):
        from app.models.briefing import Briefing, BriefingStatus
        from datetime import date

        briefing = Briefing(
            user_id=test_user.id,
            briefing_date=date.today(),
            content="Guten Morgen! Dein Wellbeing-Score ist 72/100.",
            tasks_suggested=[
                {"task_id": "abc", "title": "Wichtige Aufgabe", "priority": "high"},
            ],
            wellbeing_snapshot={"score": 72, "zone": "green"},
            status=BriefingStatus.GENERATED,
        )
        test_db.add(briefing)
        await test_db.flush()

        assert briefing.id is not None
        assert briefing.status == BriefingStatus.GENERATED
        assert briefing.read_at is None

    async def test_cascade_delete(self, test_db, test_user):
        from app.models.briefing import Briefing
        from app.models.user import User
        from datetime import date
        from sqlalchemy import select, func

        briefing = Briefing(
            user_id=test_user.id,
            briefing_date=date.today(),
            content="Test briefing",
            tasks_suggested=[],
            wellbeing_snapshot={},
        )
        test_db.add(briefing)
        await test_db.flush()

        await test_db.delete(test_user)
        await test_db.flush()

        count = await test_db.scalar(
            select(func.count()).select_from(Briefing).where(
                Briefing.user_id == test_user.id
            )
        )
        assert count == 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_models.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 3: Implement the model**

```python
# backend/app/models/briefing.py
"""Briefing model for daily Morning Briefings."""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class BriefingStatus(str, enum.Enum):
    """Status of a briefing."""

    GENERATED = "generated"
    DELIVERED = "delivered"
    READ = "read"


class Briefing(BaseModel):
    """Daily Morning Briefing for a user."""

    __tablename__ = "briefings"
    __table_args__ = {"comment": "Daily Morning Briefings"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this briefing belongs to",
    )

    briefing_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        comment="Date this briefing is for",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="LLM-generated briefing text (German)",
    )

    tasks_suggested: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Prioritized task list [{task_id, title, priority, reason}]",
    )

    wellbeing_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Wellbeing score snapshot at generation time",
    )

    status: Mapped[BriefingStatus] = mapped_column(
        String(20),
        nullable=False,
        default=BriefingStatus.GENERATED,
        comment="Briefing lifecycle status",
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When the user opened the briefing",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="briefings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Briefing(user_id={self.user_id}, date={self.briefing_date})>"
```

**Step 4: Register in `__init__.py` and add relationship to User**

Add to `backend/app/models/__init__.py`:
```python
from app.models.briefing import Briefing, BriefingStatus  # noqa: F401
```

Add to `backend/app/models/user.py` relationships:
```python
briefings: Mapped[list["Briefing"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

And add to the `TYPE_CHECKING` imports in user.py:
```python
from app.models.briefing import Briefing
```

**Step 5: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_models.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/models/briefing.py backend/app/models/__init__.py backend/app/models/user.py backend/tests/test_briefing_models.py
git commit -m "[HR-459] feat(models): add Briefing DB model with status lifecycle"
```

---

## Task 2: Alembic Migration 006

**Files:**
- Create: `backend/alembic/versions/006_phase8_briefing.py`

**Step 1: Write migration**

```python
# backend/alembic/versions/006_phase8_briefing.py
"""Phase 8 briefing: briefings table.

Revision ID: 006_phase8_briefing
Revises: 005_phase7_wellbeing
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_phase8_briefing"
down_revision: Union[str, None] = "005_phase7_wellbeing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "briefings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "briefing_date",
            sa.Date,
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "tasks_suggested",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "wellbeing_snapshot",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="generated",
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Daily Morning Briefings",
    )

    # One briefing per user per day + fast lookup
    op.create_index(
        "ix_briefings_user_date",
        "briefings",
        ["user_id", "briefing_date"],
        unique=True,
    )

    # Fast lookup for recent briefings
    op.create_index(
        "ix_briefings_user_created",
        "briefings",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_briefings_user_created", table_name="briefings")
    op.drop_index("ix_briefings_user_date", table_name="briefings")
    op.drop_table("briefings")
```

**Step 2: Commit**

```bash
git add backend/alembic/versions/006_phase8_briefing.py
git commit -m "[HR-459] db: add migration 006 for briefings table"
```

---

## Task 3: Briefing Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/briefing.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_briefing_schemas.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_briefing_schemas.py
"""Tests for briefing Pydantic schemas."""

import pytest
from datetime import datetime, date, timezone
from pydantic import ValidationError


class TestBriefingTaskItem:
    def test_valid_task_item(self):
        from app.schemas.briefing import BriefingTaskItem
        item = BriefingTaskItem(
            task_id="abc-123",
            title="Wichtige Aufgabe",
            priority="high",
            reason="Hohe Energie am Vormittag",
        )
        assert item.task_id == "abc-123"
        assert item.priority == "high"

    def test_optional_reason(self):
        from app.schemas.briefing import BriefingTaskItem
        item = BriefingTaskItem(
            task_id="abc",
            title="Test",
            priority="medium",
        )
        assert item.reason is None


class TestBriefingResponse:
    def test_valid_response(self):
        from app.schemas.briefing import BriefingResponse
        resp = BriefingResponse(
            id="uuid-here",
            briefing_date=date.today(),
            content="Guten Morgen!",
            tasks_suggested=[],
            wellbeing_snapshot={"score": 72, "zone": "green"},
            status="generated",
            read_at=None,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == "generated"

    def test_status_validation(self):
        from app.schemas.briefing import BriefingResponse
        resp = BriefingResponse(
            id="uuid",
            briefing_date=date.today(),
            content="Test",
            tasks_suggested=[],
            wellbeing_snapshot={},
            status="read",
            read_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == "read"


class TestBriefingHistoryResponse:
    def test_valid_history(self):
        from app.schemas.briefing import BriefingHistoryResponse
        history = BriefingHistoryResponse(briefings=[], days=7)
        assert history.days == 7

    def test_days_minimum(self):
        from app.schemas.briefing import BriefingHistoryResponse
        with pytest.raises(ValidationError):
            BriefingHistoryResponse(briefings=[], days=0)


class TestBrainDumpRequest:
    def test_valid_brain_dump(self):
        from app.schemas.briefing import BrainDumpRequest
        dump = BrainDumpRequest(text="Muss noch Einkaufen gehen und Arzt anrufen")
        assert len(dump.text) > 0

    def test_empty_text_rejected(self):
        from app.schemas.briefing import BrainDumpRequest
        with pytest.raises(ValidationError):
            BrainDumpRequest(text="")

    def test_max_length(self):
        from app.schemas.briefing import BrainDumpRequest
        with pytest.raises(ValidationError):
            BrainDumpRequest(text="x" * 5001)


class TestBrainDumpResponse:
    def test_valid_response(self):
        from app.schemas.briefing import BrainDumpResponse
        resp = BrainDumpResponse(
            tasks_created=2,
            tasks=[
                {"title": "Einkaufen gehen", "priority": "medium"},
                {"title": "Arzt anrufen", "priority": "high"},
            ],
            message="2 Aufgaben aus deinem Brain Dump erstellt.",
        )
        assert resp.tasks_created == 2


class TestSchemaRegistration:
    def test_schemas_in_init(self):
        from app.schemas import BriefingResponse, BrainDumpRequest
        assert BriefingResponse is not None
        assert BrainDumpRequest is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_schemas.py -v`
Expected: FAIL

**Step 3: Implement schemas**

```python
# backend/app/schemas/briefing.py
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
```

**Step 4: Register in `__init__.py`**

Add to `backend/app/schemas/__init__.py`:
```python
from app.schemas.briefing import (  # noqa: F401
    BriefingResponse,
    BriefingHistoryResponse,
    BriefingTaskItem,
    BrainDumpRequest,
    BrainDumpResponse,
)
```

**Step 5: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_schemas.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/schemas/briefing.py backend/app/schemas/__init__.py backend/tests/test_briefing_schemas.py
git commit -m "[HR-459] feat(schemas): add briefing Pydantic schemas with brain dump support"
```

---

## Task 4: BriefingService — Core Logic

**Files:**
- Create: `backend/app/services/briefing.py`
- Test: `backend/tests/test_briefing_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_briefing_service.py
"""Tests for BriefingService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timezone
from uuid import uuid4


class TestPrioritizeTasks:
    def test_sorts_by_priority(self):
        from app.services.briefing import BriefingService
        tasks = [
            MagicMock(id=uuid4(), title="Low", priority=MagicMock(value="low"), due_date=None, estimated_minutes=30, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="Urgent", priority=MagicMock(value="urgent"), due_date=None, estimated_minutes=15, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="High", priority=MagicMock(value="high"), due_date=None, estimated_minutes=45, status=MagicMock(value="open")),
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert result[0]["title"] == "Urgent"
        assert result[1]["title"] == "High"
        assert result[2]["title"] == "Low"

    def test_respects_max_tasks(self):
        from app.services.briefing import BriefingService
        tasks = [
            MagicMock(id=uuid4(), title=f"Task {i}", priority=MagicMock(value="medium"), due_date=None, estimated_minutes=30, status=MagicMock(value="open"))
            for i in range(10)
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert len(result) == 3

    def test_empty_tasks(self):
        from app.services.briefing import BriefingService
        result = BriefingService._prioritize_tasks([], max_tasks=3)
        assert result == []

    def test_due_date_boosts_priority(self):
        from app.services.briefing import BriefingService
        from datetime import timedelta
        soon = datetime.now(timezone.utc) + timedelta(hours=2)
        later = datetime.now(timezone.utc) + timedelta(days=5)
        tasks = [
            MagicMock(id=uuid4(), title="Later", priority=MagicMock(value="medium"), due_date=later, estimated_minutes=30, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="Soon", priority=MagicMock(value="medium"), due_date=soon, estimated_minutes=30, status=MagicMock(value="open")),
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert result[0]["title"] == "Soon"


class TestGenerateBriefingContent:
    def test_builds_prompt_context(self):
        from app.services.briefing import BriefingService
        tasks = [{"task_id": "a", "title": "Test", "priority": "high", "reason": None}]
        wellbeing = {"score": 72, "zone": "green", "components": {}}
        trends = {"avg_mood": 0.3, "avg_energy": 0.6, "avg_focus": 0.5, "mood_trend": "rising"}
        ctx = BriefingService._build_prompt_context(
            display_name="Oliver",
            tasks=tasks,
            wellbeing=wellbeing,
            trends=trends,
        )
        assert "Oliver" in ctx
        assert "72" in ctx
        assert "Test" in ctx


@pytest.mark.asyncio
class TestGetTodayBriefing:
    async def test_returns_none_if_no_briefing(self):
        from app.services.briefing import BriefingService
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        service = BriefingService(mock_db)
        result = await service.get_today_briefing(str(uuid4()))
        assert result is None


@pytest.mark.asyncio
class TestMarkAsRead:
    async def test_marks_briefing_read(self):
        from app.services.briefing import BriefingService, BriefingStatus
        mock_db = AsyncMock()
        mock_briefing = MagicMock()
        mock_briefing.status = "generated"
        mock_briefing.read_at = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_briefing
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BriefingService(mock_db)
        result = await service.mark_as_read(str(uuid4()), str(uuid4()))
        assert result is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_service.py -v`
Expected: FAIL

**Step 3: Implement BriefingService**

```python
# backend/app/services/briefing.py
"""BriefingService for generating personalized Morning Briefings."""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.briefing import Briefing, BriefingStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.services.pattern_analyzer import PatternAnalyzer
from app.services.wellbeing import WellbeingService

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {
    "urgent": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

BRIEFING_SYSTEM_PROMPT = """Du bist Alice, ein einfuehlsamer ADHS-Coach. Erstelle ein kurzes, motivierendes Morning Briefing auf Deutsch.

Regeln:
- Maximal 150 Woerter
- Beginne mit einer persoenlichen Begruessung
- Erwaehne den Wellbeing-Score und den Trend
- Nenne die Top-Aufgaben (max 3) mit kurzer Begruendung
- Gib einen ADHS-spezifischen Tipp basierend auf den Trends
- Verwende einen warmen, ermutigenden Ton
- KEINE Emojis"""


class BriefingService:
    """Service for generating and managing Morning Briefings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)
        self.wellbeing_service = WellbeingService(db)

    async def generate_briefing(
        self, user_id: str, display_name: str | None = None, max_tasks: int = 3
    ) -> dict[str, Any]:
        """Generate a new Morning Briefing for today."""
        # 1. Get open tasks
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == UUID(user_id),
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        )
        all_tasks = result.scalars().all()

        # 2. Prioritize tasks
        prioritized = self._prioritize_tasks(all_tasks, max_tasks=max_tasks)

        # 3. Get wellbeing data
        wellbeing = await self.wellbeing_service.get_latest_score(user_id)
        if not wellbeing:
            wellbeing = {"score": 50, "zone": "yellow", "components": {}}

        # 4. Get recent trends
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)

        # 5. Build prompt context and generate LLM content
        context = self._build_prompt_context(
            display_name=display_name or "du",
            tasks=prioritized,
            wellbeing=wellbeing,
            trends=trends,
        )
        content = await self._generate_with_llm(context)

        # 6. Persist briefing
        briefing = Briefing(
            user_id=UUID(user_id),
            briefing_date=date.today(),
            content=content,
            tasks_suggested=prioritized,
            wellbeing_snapshot=wellbeing,
            status=BriefingStatus.GENERATED,
        )
        self.db.add(briefing)
        await self.db.flush()

        return {
            "id": str(briefing.id),
            "briefing_date": briefing.briefing_date,
            "content": content,
            "tasks_suggested": prioritized,
            "wellbeing_snapshot": wellbeing,
            "status": briefing.status,
            "read_at": None,
            "created_at": briefing.created_at,
        }

    async def get_today_briefing(self, user_id: str) -> dict[str, Any] | None:
        """Get today's briefing if it exists."""
        result = await self.db.execute(
            select(Briefing).where(
                Briefing.user_id == UUID(user_id),
                Briefing.briefing_date == date.today(),
            )
        )
        briefing = result.scalar_one_or_none()
        if not briefing:
            return None

        return {
            "id": str(briefing.id),
            "briefing_date": briefing.briefing_date,
            "content": briefing.content,
            "tasks_suggested": briefing.tasks_suggested,
            "wellbeing_snapshot": briefing.wellbeing_snapshot,
            "status": briefing.status,
            "read_at": briefing.read_at,
            "created_at": briefing.created_at,
        }

    async def get_briefing_history(self, user_id: str, days: int = 7) -> list[dict]:
        """Get briefing history for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(Briefing)
            .where(
                Briefing.user_id == UUID(user_id),
                Briefing.created_at >= cutoff,
            )
            .order_by(Briefing.briefing_date.desc())
        )
        briefings = result.scalars().all()
        return [
            {
                "id": str(b.id),
                "briefing_date": b.briefing_date,
                "content": b.content,
                "tasks_suggested": b.tasks_suggested,
                "wellbeing_snapshot": b.wellbeing_snapshot,
                "status": b.status,
                "read_at": b.read_at,
                "created_at": b.created_at,
            }
            for b in briefings
        ]

    async def mark_as_read(self, briefing_id: str, user_id: str) -> bool:
        """Mark a briefing as read."""
        result = await self.db.execute(
            select(Briefing).where(
                Briefing.id == UUID(briefing_id),
                Briefing.user_id == UUID(user_id),
            )
        )
        briefing = result.scalar_one_or_none()
        if not briefing:
            return False

        briefing.status = BriefingStatus.READ
        briefing.read_at = datetime.now(timezone.utc)
        return True

    @staticmethod
    def _prioritize_tasks(
        tasks: list, max_tasks: int = 3
    ) -> list[dict[str, Any]]:
        """Prioritize tasks by urgency and due date (ADHS-optimized: max N tasks)."""
        if not tasks:
            return []

        def sort_key(task):
            prio = PRIORITY_ORDER.get(task.priority.value, 2)
            # Boost tasks with soon due dates
            if task.due_date:
                hours_until = (task.due_date - datetime.now(timezone.utc)).total_seconds() / 3600
                if hours_until < 24:
                    prio -= 2
                elif hours_until < 72:
                    prio -= 1
            return prio

        sorted_tasks = sorted(tasks, key=sort_key)

        return [
            {
                "task_id": str(t.id),
                "title": t.title,
                "priority": t.priority.value,
                "reason": _reason_for_task(t),
            }
            for t in sorted_tasks[:max_tasks]
        ]

    @staticmethod
    def _build_prompt_context(
        display_name: str,
        tasks: list[dict],
        wellbeing: dict,
        trends: dict,
    ) -> str:
        """Build context string for the LLM prompt."""
        task_lines = ""
        for i, t in enumerate(tasks, 1):
            reason = f" — {t['reason']}" if t.get("reason") else ""
            task_lines += f"  {i}. {t['title']} (Prioritaet: {t['priority']}){reason}\n"

        if not task_lines:
            task_lines = "  Keine offenen Aufgaben.\n"

        mood_trend = trends.get("mood_trend", "stable")
        energy = trends.get("avg_energy", 0.5)
        score = wellbeing.get("score", 50)
        zone = wellbeing.get("zone", "yellow")

        return f"""Name: {display_name}
Wellbeing-Score: {score:.0f}/100 (Zone: {zone})
Stimmungstrend: {mood_trend}
Durchschnittliche Energie: {energy:.0%}
Heutige Aufgaben:
{task_lines}"""

    async def _generate_with_llm(self, context: str) -> str:
        """Generate briefing content using Claude API."""
        from app.core.config import settings

        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            # Fallback: generate a simple template-based briefing
            return self._generate_fallback(context)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 500,
                        "system": BRIEFING_SYSTEM_PROMPT,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Erstelle ein Morning Briefing mit diesem Kontext:\n\n{context}",
                            }
                        ],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
        except Exception:
            logger.exception("LLM briefing generation failed, using fallback")
            return self._generate_fallback(context)

    @staticmethod
    def _generate_fallback(context: str) -> str:
        """Generate a simple template-based briefing when LLM is unavailable."""
        lines = context.strip().split("\n")
        name = "du"
        score_line = ""
        for line in lines:
            if line.startswith("Name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("Wellbeing-Score:"):
                score_line = line.split(":", 1)[1].strip()

        return (
            f"Guten Morgen {name}!\n\n"
            f"Dein Wellbeing-Score: {score_line}\n\n"
            f"Konzentriere dich heute auf deine wichtigsten Aufgaben. "
            f"Mach Pausen wenn du sie brauchst und sei nicht zu streng mit dir."
        )


def _reason_for_task(task) -> str | None:
    """Generate a short reason why this task is prioritized."""
    if task.due_date:
        hours = (task.due_date - datetime.now(timezone.utc)).total_seconds() / 3600
        if hours < 0:
            return "Ueberfaellig"
        elif hours < 24:
            return "Faellig heute"
        elif hours < 72:
            return "Faellig in den naechsten Tagen"
    if task.priority.value == "urgent":
        return "Dringend"
    return None
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_service.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/briefing.py backend/tests/test_briefing_service.py
git commit -m "[HR-459] feat(services): add BriefingService with LLM generation and task prioritization"
```

---

## Task 5: Brain Dump Service

**Files:**
- Create: `backend/app/services/brain_dump.py`
- Test: `backend/tests/test_brain_dump.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_brain_dump.py
"""Tests for BrainDumpService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestParseBrainDump:
    def test_splits_by_und(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen gehen und Arzt anrufen")
        assert len(items) == 2
        assert "Einkaufen gehen" in items
        assert "Arzt anrufen" in items

    def test_splits_by_newline(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen\nArzt anrufen\nSport")
        assert len(items) == 3

    def test_splits_by_comma(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen, Arzt, Sport")
        assert len(items) == 3

    def test_strips_whitespace(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("  Einkaufen  ,  Arzt  ")
        assert items[0] == "Einkaufen"

    def test_removes_empty(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen,,, Arzt")
        assert len(items) == 2

    def test_single_item(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen gehen")
        assert len(items) == 1
        assert items[0] == "Einkaufen gehen"

    def test_numbered_list(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("1. Einkaufen\n2. Arzt\n3. Sport")
        assert len(items) == 3
        assert items[0] == "Einkaufen"


@pytest.mark.asyncio
class TestProcessBrainDump:
    async def test_creates_tasks(self):
        from app.services.brain_dump import BrainDumpService
        mock_db = AsyncMock()
        service = BrainDumpService(mock_db)
        result = await service.process(str(uuid4()), "Einkaufen, Arzt anrufen")
        assert result["tasks_created"] == 2
        assert len(result["tasks"]) == 2
        assert mock_db.add.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_brain_dump.py -v`
Expected: FAIL

**Step 3: Implement BrainDumpService**

```python
# backend/app/services/brain_dump.py
"""BrainDumpService for quick thought capture and task creation."""

import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


class BrainDumpService:
    """Parses free-text brain dumps into structured tasks."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process(self, user_id: str, text: str) -> dict[str, Any]:
        """Parse brain dump text and create tasks."""
        items = self._parse_text(text)
        created = []

        for item in items:
            task = Task(
                user_id=UUID(user_id),
                title=item[:200],  # Cap title length
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.OPEN,
            )
            self.db.add(task)
            created.append({"title": task.title, "priority": task.priority.value})

        await self.db.flush()

        return {
            "tasks_created": len(created),
            "tasks": created,
            "message": f"{len(created)} Aufgabe{'n' if len(created) != 1 else ''} aus deinem Brain Dump erstellt.",
        }

    @staticmethod
    def _parse_text(text: str) -> list[str]:
        """Parse free-text into individual task items."""
        # Remove numbered list prefixes (1. 2. 3. or - or *)
        text = re.sub(r"^\s*[\d]+[.)]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.MULTILINE)

        # Split by newlines first
        if "\n" in text:
            items = text.split("\n")
        # Then by " und " (German "and")
        elif " und " in text:
            items = text.split(" und ")
        # Then by commas
        elif "," in text:
            items = text.split(",")
        else:
            items = [text]

        # Clean up
        return [item.strip() for item in items if item.strip()]
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_brain_dump.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/brain_dump.py backend/tests/test_brain_dump.py
git commit -m "[HR-459] feat(services): add BrainDumpService for quick task capture"
```

---

## Task 6: Briefing API Endpoints

**Files:**
- Create: `backend/app/api/v1/briefing.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_briefing_api.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_briefing_api.py
"""Tests for briefing API endpoints."""

import pytest


class TestBriefingRouterRegistered:
    def test_briefing_prefix_in_v1_router(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/briefing" in p for p in paths)


class TestBriefingEndpointsExist:
    def test_router_has_today_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/today" in paths

    def test_router_has_generate_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/generate" in paths

    def test_router_has_history_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/history" in paths

    def test_router_has_read_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert any("read" in p for p in paths)

    def test_router_has_brain_dump_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/brain-dump" in paths

    def test_today_is_get(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/today":
                assert "GET" in route.methods

    def test_generate_is_post(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/generate":
                assert "POST" in route.methods

    def test_brain_dump_is_post(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/brain-dump":
                assert "POST" in route.methods
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_api.py -v`
Expected: FAIL

**Step 3: Implement API endpoints**

```python
# backend/app/api/v1/briefing.py
"""Morning Briefing API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.models.user_settings import DEFAULT_SETTINGS
from app.schemas.briefing import (
    BriefingResponse,
    BriefingHistoryResponse,
    BrainDumpRequest,
    BrainDumpResponse,
)
from app.services.briefing import BriefingService
from app.services.brain_dump import BrainDumpService

router = APIRouter(tags=["Briefing"])


@router.get(
    "/today",
    response_model=BriefingResponse | None,
    summary="Get today's Morning Briefing",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_today_briefing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's briefing if it exists. Returns null if not yet generated."""
    service = BriefingService(db)
    return await service.get_today_briefing(str(current_user.id))


@router.post(
    "/generate",
    response_model=BriefingResponse,
    summary="Generate today's Morning Briefing",
    dependencies=[Depends(standard_rate_limit)],
)
async def generate_briefing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new Morning Briefing for today (or return existing one)."""
    service = BriefingService(db)

    # Check if already exists
    existing = await service.get_today_briefing(str(current_user.id))
    if existing:
        return BriefingResponse(**existing)

    # Get user settings for display_name and max_daily_tasks
    settings = {}
    if current_user.user_settings:
        settings = {**DEFAULT_SETTINGS, **current_user.user_settings.settings}
    display_name = settings.get("display_name")
    max_tasks = settings.get("max_daily_tasks", 3)

    result = await service.generate_briefing(
        str(current_user.id),
        display_name=display_name,
        max_tasks=max_tasks,
    )
    await db.commit()
    return BriefingResponse(**result)


@router.get(
    "/history",
    response_model=BriefingHistoryResponse,
    summary="Get briefing history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_briefing_history(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get briefing history for the last N days."""
    service = BriefingService(db)
    briefings = await service.get_briefing_history(str(current_user.id), days=days)
    return BriefingHistoryResponse(
        briefings=[BriefingResponse(**b) for b in briefings],
        days=days,
    )


@router.put(
    "/{briefing_id}/read",
    summary="Mark briefing as read",
    dependencies=[Depends(standard_rate_limit)],
)
async def mark_briefing_read(
    briefing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a briefing as read."""
    service = BriefingService(db)
    success = await service.mark_as_read(briefing_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Briefing not found")
    await db.commit()
    return {"status": "read"}


@router.post(
    "/brain-dump",
    response_model=BrainDumpResponse,
    summary="Process brain dump into tasks",
    dependencies=[Depends(standard_rate_limit)],
)
async def brain_dump(
    data: BrainDumpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse free-text brain dump and create tasks automatically."""
    service = BrainDumpService(db)
    result = await service.process(str(current_user.id), data.text)
    await db.commit()
    return BrainDumpResponse(**result)
```

**Step 4: Register in router.py**

Add to `backend/app/api/v1/router.py` imports:
```python
from app.api.v1 import briefing
```

Add after the wellbeing router:
```python
# Phase 8: Morning Briefing routers
router.include_router(briefing.router, prefix="/briefing", tags=["Briefing"])
```

**Step 5: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_api.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/api/v1/briefing.py backend/app/api/v1/router.py backend/tests/test_briefing_api.py
git commit -m "[HR-459] feat(api): add briefing API endpoints (today, generate, history, brain-dump)"
```

---

## Task 7: Scheduler Integration — Morning Briefing Cron

**Files:**
- Modify: `backend/app/services/scheduler.py`
- Test: `backend/tests/test_briefing_scheduler.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_briefing_scheduler.py
"""Tests for briefing scheduler integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestBriefingSchedulerFunction:
    def test_function_exists(self):
        from app.services.scheduler import _process_morning_briefing
        assert callable(_process_morning_briefing)

    @pytest.mark.asyncio
    async def test_generates_briefing_at_configured_time(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": True,
            "briefing_time": "07:00",
            "display_name": "Oliver",
            "max_daily_tasks": 3,
        }
        with patch("app.services.scheduler.BriefingService") as MockBS, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession, \
             patch("app.services.scheduler._is_near_reminder_time", return_value=True):
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockBS.return_value.get_today_briefing = AsyncMock(return_value=None)
            MockBS.return_value.generate_briefing = AsyncMock(
                return_value={"content": "Guten Morgen!", "id": "abc"}
            )
            await _process_morning_briefing(user_id, settings)
            MockBS.return_value.generate_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_productivity_not_active(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {"active_modules": ["core", "adhs"], "morning_briefing": True}
        with patch("app.services.scheduler.BriefingService") as MockBS:
            await _process_morning_briefing(user_id, settings)
            MockBS.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_briefing_disabled(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": False,
        }
        with patch("app.services.scheduler.BriefingService") as MockBS:
            await _process_morning_briefing(user_id, settings)
            MockBS.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_already_generated(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": True,
            "briefing_time": "07:00",
        }
        with patch("app.services.scheduler.BriefingService") as MockBS, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession, \
             patch("app.services.scheduler._is_near_reminder_time", return_value=True):
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockBS.return_value.get_today_briefing = AsyncMock(
                return_value={"id": "exists", "content": "Already done"}
            )
            await _process_morning_briefing(user_id, settings)
            MockBS.return_value.generate_briefing.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_scheduler.py -v`
Expected: FAIL

**Step 3: Add morning briefing to scheduler**

Add to `backend/app/services/scheduler.py`:

1. Add import after existing wellbeing imports:
```python
from app.services.briefing import BriefingService
```

2. Add function before `_is_quiet_hours`:
```python
async def _process_morning_briefing(user_id: UUID, settings: dict) -> None:
    """Generate and deliver Morning Briefing if productivity module is active."""
    active_modules = settings.get("active_modules", ["core", "adhs"])
    if "productivity" not in active_modules:
        return

    if not settings.get("morning_briefing", True):
        return

    # Check if we're near the briefing time
    briefing_time = settings.get("briefing_time", "07:00")
    now_berlin = datetime.now(BERLIN_TZ)
    if not _is_near_reminder_time(now_berlin, [briefing_time], window_minutes=5):
        return

    async with AsyncSessionLocal() as db:
        service = BriefingService(db)

        # Don't regenerate if already exists for today
        existing = await service.get_today_briefing(str(user_id))
        if existing:
            return

        display_name = settings.get("display_name")
        max_tasks = settings.get("max_daily_tasks", 3)

        result = await service.generate_briefing(
            str(user_id), display_name=display_name, max_tasks=max_tasks
        )
        await db.commit()

        # Send push notification
        token = settings.get("expo_push_token")
        if token:
            await NotificationService.send_notification(
                PushNotification(
                    to=token,
                    title="Dein Morning Briefing",
                    body=result["content"][:100] + "...",
                    data={"type": "briefing", "id": result["id"]},
                )
            )
```

3. Add call at end of `_process_user`:
```python
    # 5. Morning Briefing (if productivity module active)
    try:
        await _process_morning_briefing(user_id, settings)
    except Exception:
        logger.exception("Morning briefing error for user %s", user_id)
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_briefing_scheduler.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/scheduler.py backend/tests/test_briefing_scheduler.py
git commit -m "[HR-459] feat(scheduler): add Morning Briefing generation cron job"
```

---

## Task 8: Mobile — Briefing API Service & Zustand Store

**Files:**
- Create: `mobile/services/briefing.ts`
- Create: `mobile/stores/briefingStore.ts`

**Step 1: Create API service**

```typescript
// mobile/services/briefing.ts
import api from "./api";

export interface BriefingTaskItem {
  task_id: string;
  title: string;
  priority: string;
  reason: string | null;
}

export interface BriefingData {
  id: string;
  briefing_date: string;
  content: string;
  tasks_suggested: BriefingTaskItem[];
  wellbeing_snapshot: Record<string, number | string>;
  status: string;
  read_at: string | null;
  created_at: string;
}

export interface BrainDumpResult {
  tasks_created: number;
  tasks: Array<{ title: string; priority: string }>;
  message: string;
}

export const briefingApi = {
  getToday: () =>
    api.get<BriefingData | null>("/briefing/today").then((r) => r.data),

  generate: () =>
    api.post<BriefingData>("/briefing/generate").then((r) => r.data),

  getHistory: (days = 7) =>
    api
      .get<{ briefings: BriefingData[]; days: number }>(
        `/briefing/history?days=${days}`
      )
      .then((r) => r.data),

  markAsRead: (id: string) =>
    api.put(`/briefing/${id}/read`),

  brainDump: (text: string) =>
    api
      .post<BrainDumpResult>("/briefing/brain-dump", { text })
      .then((r) => r.data),
};
```

**Step 2: Create Zustand store**

```typescript
// mobile/stores/briefingStore.ts
import { create } from "zustand";
import {
  briefingApi,
  BriefingData,
  BrainDumpResult,
} from "../services/briefing";

interface BriefingState {
  briefing: BriefingData | null;
  isLoading: boolean;
  error: string | null;
  fetchToday: () => Promise<void>;
  generateBriefing: () => Promise<void>;
  markAsRead: () => Promise<void>;
  submitBrainDump: (text: string) => Promise<BrainDumpResult | null>;
}

export const useBriefingStore = create<BriefingState>((set, get) => ({
  briefing: null,
  isLoading: false,
  error: null,

  fetchToday: async () => {
    set({ isLoading: true, error: null });
    try {
      const briefing = await briefingApi.getToday();
      set({ briefing, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  generateBriefing: async () => {
    set({ isLoading: true, error: null });
    try {
      const briefing = await briefingApi.generate();
      set({ briefing, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  markAsRead: async () => {
    const { briefing } = get();
    if (!briefing) return;
    try {
      await briefingApi.markAsRead(briefing.id);
      set({ briefing: { ...briefing, status: "read" } });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  submitBrainDump: async (text: string) => {
    try {
      const result = await briefingApi.brainDump(text);
      return result;
    } catch (e: any) {
      set({ error: e.message });
      return null;
    }
  },
}));
```

**Step 3: Commit**

```bash
git add mobile/services/briefing.ts mobile/stores/briefingStore.ts
git commit -m "[HR-459] feat(mobile): add briefing API service and Zustand store"
```

---

## Task 9: Mobile — Briefing Tab Screen

**Files:**
- Create: `mobile/app/(tabs)/briefing/_layout.tsx`
- Create: `mobile/app/(tabs)/briefing/index.tsx`
- Modify: `mobile/app/(tabs)/_layout.tsx` (add briefing tab)

**Step 1: Create briefing tab layout**

```typescript
// mobile/app/(tabs)/briefing/_layout.tsx
import { Stack } from "expo-router";

export default function BriefingLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
```

**Step 2: Create briefing index screen**

```typescript
// mobile/app/(tabs)/briefing/index.tsx
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  useColorScheme,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useBriefingStore } from "../../../stores/briefingStore";

const PRIORITY_COLORS: Record<string, string> = {
  urgent: "#ef4444",
  high: "#f59e0b",
  medium: "#0284c7",
  low: "#6b7280",
};

export default function BriefingScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const {
    briefing,
    isLoading,
    fetchToday,
    generateBriefing,
    markAsRead,
    submitBrainDump,
  } = useBriefingStore();

  const [brainDumpText, setBrainDumpText] = useState("");
  const [brainDumpResult, setBrainDumpResult] = useState<string | null>(null);

  useEffect(() => {
    fetchToday();
  }, []);

  useEffect(() => {
    if (briefing && briefing.status !== "read") {
      markAsRead();
    }
  }, [briefing?.id]);

  const handleRefresh = useCallback(() => {
    fetchToday();
  }, [fetchToday]);

  const handleGenerate = useCallback(async () => {
    await generateBriefing();
  }, [generateBriefing]);

  const handleBrainDump = useCallback(async () => {
    if (!brainDumpText.trim()) return;
    const result = await submitBrainDump(brainDumpText.trim());
    if (result) {
      setBrainDumpResult(result.message);
      setBrainDumpText("");
      setTimeout(() => setBrainDumpResult(null), 3000);
    }
  }, [brainDumpText, submitBrainDump]);

  if (isLoading && !briefing) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        style={{ flex: 1, backgroundColor: isDark ? "#030712" : "#f9fafb" }}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
        }
      >
        {/* No Briefing Yet */}
        {!briefing && (
          <Card style={{ marginBottom: 16 }}>
            <View style={{ padding: 20, alignItems: "center" }}>
              <Ionicons
                name="sunny-outline"
                size={48}
                color={isDark ? "#fcd34d" : "#f59e0b"}
              />
              <Text
                style={{
                  fontSize: 18,
                  fontWeight: "700",
                  color: isDark ? "#f9fafb" : "#111827",
                  marginTop: 12,
                }}
              >
                Kein Briefing fuer heute
              </Text>
              <TouchableOpacity
                onPress={handleGenerate}
                style={{
                  marginTop: 16,
                  paddingVertical: 10,
                  paddingHorizontal: 24,
                  borderRadius: 8,
                  backgroundColor: "#0284c7",
                }}
              >
                <Text style={{ color: "#fff", fontWeight: "600" }}>
                  Briefing generieren
                </Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {/* Briefing Content */}
        {briefing && (
          <Card style={{ marginBottom: 16 }}>
            <View style={{ padding: 16 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Ionicons name="sunny" size={24} color="#f59e0b" />
                <Text
                  style={{
                    fontSize: 18,
                    fontWeight: "700",
                    color: isDark ? "#f9fafb" : "#111827",
                  }}
                >
                  Morning Briefing
                </Text>
              </View>
              <Text
                style={{
                  fontSize: 15,
                  lineHeight: 22,
                  color: isDark ? "#d1d5db" : "#374151",
                }}
              >
                {briefing.content}
              </Text>
            </View>
          </Card>
        )}

        {/* Task Cards */}
        {briefing && briefing.tasks_suggested.length > 0 && (
          <View style={{ marginBottom: 16 }}>
            <Text
              style={{
                fontSize: 16,
                fontWeight: "700",
                color: isDark ? "#f9fafb" : "#111827",
                marginBottom: 8,
              }}
            >
              Deine Top-Aufgaben
            </Text>
            {briefing.tasks_suggested.map((task: any, index: number) => (
              <Card key={task.task_id || index} style={{ marginBottom: 8 }}>
                <View style={{ padding: 12, flexDirection: "row", alignItems: "center", gap: 12 }}>
                  <View
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 16,
                      backgroundColor: PRIORITY_COLORS[task.priority] || "#6b7280",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: 14 }}>
                      {index + 1}
                    </Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text
                      style={{
                        fontSize: 15,
                        fontWeight: "600",
                        color: isDark ? "#f9fafb" : "#111827",
                      }}
                    >
                      {task.title}
                    </Text>
                    {task.reason && (
                      <Text
                        style={{
                          fontSize: 12,
                          color: isDark ? "#9ca3af" : "#6b7280",
                          marginTop: 2,
                        }}
                      >
                        {task.reason}
                      </Text>
                    )}
                  </View>
                </View>
              </Card>
            ))}
          </View>
        )}

        {/* Brain Dump */}
        <Card style={{ marginBottom: 16 }}>
          <View style={{ padding: 16 }}>
            <Text
              style={{
                fontSize: 16,
                fontWeight: "700",
                color: isDark ? "#f9fafb" : "#111827",
                marginBottom: 8,
              }}
            >
              Brain Dump
            </Text>
            <TextInput
              value={brainDumpText}
              onChangeText={setBrainDumpText}
              placeholder="Gedanken loswerden... (kommagetrennt oder neue Zeile)"
              placeholderTextColor={isDark ? "#6b7280" : "#9ca3af"}
              multiline
              numberOfLines={3}
              style={{
                backgroundColor: isDark ? "#1f2937" : "#f3f4f6",
                borderRadius: 8,
                padding: 12,
                color: isDark ? "#f9fafb" : "#111827",
                fontSize: 14,
                minHeight: 80,
                textAlignVertical: "top",
              }}
            />
            {brainDumpResult && (
              <Text style={{ color: "#16a34a", marginTop: 8, fontSize: 13 }}>
                {brainDumpResult}
              </Text>
            )}
            <TouchableOpacity
              onPress={handleBrainDump}
              disabled={!brainDumpText.trim()}
              style={{
                marginTop: 10,
                paddingVertical: 10,
                borderRadius: 8,
                backgroundColor: brainDumpText.trim() ? "#0284c7" : isDark ? "#374151" : "#e5e7eb",
                alignItems: "center",
              }}
            >
              <Text
                style={{
                  color: brainDumpText.trim() ? "#fff" : isDark ? "#6b7280" : "#9ca3af",
                  fontWeight: "600",
                  fontSize: 14,
                }}
              >
                Aufgaben erstellen
              </Text>
            </TouchableOpacity>
          </View>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
```

**Step 3: Add briefing tab to TAB_CONFIG**

In `mobile/app/(tabs)/_layout.tsx`, add BEFORE dashboard in TAB_CONFIG:

```typescript
{
  name: "briefing",
  title: "Briefing",
  icon: "sunny-outline",
  requiredModules: ["productivity"],
},
```

**Step 4: Commit**

```bash
git add mobile/app/\(tabs\)/briefing/_layout.tsx mobile/app/\(tabs\)/briefing/index.tsx mobile/app/\(tabs\)/_layout.tsx
git commit -m "[HR-459] feat(mobile): add Briefing tab with brain dump and task cards"
```

---

## Task 10: Run Full Test Suite & Fix Issues

**Step 1: Run all backend tests**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All new Phase 8 tests pass, pre-existing failures unchanged

**Step 2: Fix any issues found in Phase 8 test files**

**Step 3: Commit fixes if needed**

---

## Task 11: Linear Status Update

Update Linear:
- Create epic "Morning Briefing & Adaptive Planning" under Phase 8 milestone
- Set all Phase 8 tasks to Done
- Add completion comments with file lists and acceptance criteria

---

## Task 12: Update Design Doc Checklist

**Files:**
- Modify: `docs/plans/2026-02-14-alice-agent-one-transformation-design.md`

Mark Milestone 3 items as done:

```markdown
### Milestone 3: Morning Briefing & Adaptive Planning
- [x] `Briefing` DB Model + Migration
- [x] `BriefingService` mit LLM-Generierung
- [ ] Graphiti-Context fuer Briefing-Personalisierung (Follow-up: requires deeper Graphiti integration)
- [x] Cron Job: Briefing-Generierung um konfigurierbare Zeit
- [x] Push Notification: "Briefing ist fertig"
- [x] Energie-basierte Task-Priorisierung
- [x] Max-3-Tasks Regel (ADHS-Modul)
- [x] Brain Dump Quick-Capture Feature
- [x] API: briefings/today, briefings/history
- [x] Expo: Briefing Screen (erster Tab wenn aktiviert)
- [ ] Expo: Swipeable Task Cards (Follow-up: requires gesture handler)
- [x] Expo: Brain Dump Input
```

**Commit:**

```bash
git add docs/plans/2026-02-14-alice-agent-one-transformation-design.md
git commit -m "[HR-459] docs: update design doc with Phase 8 completion status"
```
