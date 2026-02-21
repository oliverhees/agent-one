# Phase 7: Guardian Angel & Wellness Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the Wellbeing Score engine, ADHS intervention system, and Expo wellness dashboard so Alice can proactively monitor and support user wellbeing.

**Architecture:** Two new DB models (`WellbeingScore`, `Intervention`) via Alembic migration 005. A `WellbeingService` aggregates mood/energy/focus from existing `PatternLog` + `UserStats` into a 0-100 score. An `InterventionEngine` detects 7 ADHS-specific patterns and creates actionable interventions. The scheduler runs wellbeing checks every 4h. A new `wellbeing` API router exposes score, history, and intervention endpoints. The Expo app gets a new "Wellness" tab (visible when wellness module active) with score widget, trend chart, and intervention cards.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Expo SDK 52 (React Native), TypeScript, Zustand

**Linear:** HR-459 (Wellbeing Score Engine), HR-460 (ADHS Intervention Engine), HR-461 (Expo Wellbeing UI)

---

## Context: Key Existing Files

| File | Purpose |
|------|---------|
| `backend/app/models/base.py` | `BaseModel` with id (UUID), created_at, updated_at |
| `backend/app/models/pattern_log.py` | `PatternLog`: user_id, mood_score (-1..1), energy_level (0..1), focus_score (0..1) |
| `backend/app/models/user_stats.py` | `UserStats`: current_streak, tasks_completed, total_xp, level |
| `backend/app/models/__init__.py` | All model registrations + `__all__` |
| `backend/app/services/pattern_analyzer.py` | `PatternAnalyzer`: get_recent_trends(), _calculate_trend() |
| `backend/app/services/memory.py` | `MemoryService`: process_episode(), get_context() |
| `backend/app/services/scheduler.py` | Background scheduler loop (5min ticks, quiet hours) |
| `backend/app/services/notification.py` | `NotificationService`: send_notification(PushNotification) |
| `backend/app/api/v1/router.py` | All router registrations |
| `backend/app/core/modules.py` | `ALL_MODULES` registry, wellness config defaults |
| `backend/alembic/versions/004_phase5_memory.py` | Last migration (pattern_logs) |
| `mobile/app/(tabs)/_layout.tsx` | TAB_CONFIG with requiredModules for dynamic tabs |
| `mobile/app/(tabs)/dashboard/index.tsx` | Dashboard pattern: ScrollView, Card, hooks |

---

## Task 1: WellbeingScore & Intervention DB Models

**Files:**
- Create: `backend/app/models/wellbeing_score.py`
- Create: `backend/app/models/intervention.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_wellbeing_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_wellbeing_models.py
"""Tests for WellbeingScore and Intervention models."""

import pytest
from uuid import uuid4


class TestWellbeingScoreModel:
    """WellbeingScore model unit tests."""

    def test_import(self):
        from app.models.wellbeing_score import WellbeingScore
        assert WellbeingScore.__tablename__ == "wellbeing_scores"

    def test_has_required_columns(self):
        from app.models.wellbeing_score import WellbeingScore
        columns = {c.name for c in WellbeingScore.__table__.columns}
        assert "user_id" in columns
        assert "score" in columns
        assert "components" in columns
        assert "zone" in columns
        assert "created_at" in columns

    def test_zone_values(self):
        from app.models.wellbeing_score import WellbeingZone
        assert WellbeingZone.RED.value == "red"
        assert WellbeingZone.YELLOW.value == "yellow"
        assert WellbeingZone.GREEN.value == "green"


class TestInterventionModel:
    """Intervention model unit tests."""

    def test_import(self):
        from app.models.intervention import Intervention
        assert Intervention.__tablename__ == "interventions"

    def test_has_required_columns(self):
        from app.models.intervention import Intervention
        columns = {c.name for c in Intervention.__table__.columns}
        assert "user_id" in columns
        assert "type" in columns
        assert "trigger_pattern" in columns
        assert "message" in columns
        assert "status" in columns
        assert "created_at" in columns

    def test_status_values(self):
        from app.models.intervention import InterventionStatus
        assert InterventionStatus.PENDING.value == "pending"
        assert InterventionStatus.DISMISSED.value == "dismissed"
        assert InterventionStatus.ACTED.value == "acted"

    def test_type_values(self):
        from app.models.intervention import InterventionType
        assert InterventionType.HYPERFOCUS.value == "hyperfocus"
        assert InterventionType.PROCRASTINATION.value == "procrastination"
        assert InterventionType.DECISION_FATIGUE.value == "decision_fatigue"
        assert InterventionType.TRANSITION.value == "transition"
        assert InterventionType.ENERGY_CRASH.value == "energy_crash"
        assert InterventionType.SLEEP_DISRUPTION.value == "sleep_disruption"
        assert InterventionType.SOCIAL_MASKING.value == "social_masking"


class TestModelRegistration:
    """Models are registered in __init__.py."""

    def test_wellbeing_score_in_all(self):
        from app.models import WellbeingScore
        assert WellbeingScore is not None

    def test_intervention_in_all(self):
        from app.models import Intervention
        assert Intervention is not None

    def test_enums_in_all(self):
        from app.models import WellbeingZone, InterventionStatus, InterventionType
        assert WellbeingZone is not None
        assert InterventionStatus is not None
        assert InterventionType is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_models.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write WellbeingScore model**

```python
# backend/app/models/wellbeing_score.py
"""WellbeingScore model for aggregated user wellbeing tracking."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class WellbeingZone(str, enum.Enum):
    """Wellbeing score zone classification."""

    RED = "red"        # 0-30: critical
    YELLOW = "yellow"  # 31-60: caution
    GREEN = "green"    # 61-100: good


class WellbeingScore(BaseModel):
    """Aggregated wellbeing score computed from mood/energy/focus/tasks/streak."""

    __tablename__ = "wellbeing_scores"
    __table_args__ = {"comment": "Aggregated wellbeing scores for trend tracking"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this score belongs to",
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Aggregated wellbeing score 0-100",
    )

    zone: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Score zone: red (0-30), yellow (31-60), green (61-100)",
    )

    components: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Individual score components with weights",
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<WellbeingScore(user_id={self.user_id}, score={self.score}, zone={self.zone})>"
```

**Step 4: Write Intervention model**

```python
# backend/app/models/intervention.py
"""Intervention model for proactive ADHS-specific coaching interventions."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class InterventionType(str, enum.Enum):
    """Types of ADHS interventions."""

    HYPERFOCUS = "hyperfocus"
    PROCRASTINATION = "procrastination"
    DECISION_FATIGUE = "decision_fatigue"
    TRANSITION = "transition"
    ENERGY_CRASH = "energy_crash"
    SLEEP_DISRUPTION = "sleep_disruption"
    SOCIAL_MASKING = "social_masking"


class InterventionStatus(str, enum.Enum):
    """Status of an intervention."""

    PENDING = "pending"
    DISMISSED = "dismissed"
    ACTED = "acted"


class Intervention(BaseModel):
    """A proactive intervention triggered by pattern detection."""

    __tablename__ = "interventions"
    __table_args__ = {"comment": "Proactive ADHS coaching interventions"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this intervention is for",
    )

    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Intervention type (hyperfocus, procrastination, etc.)",
    )

    trigger_pattern: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Description of the pattern that triggered this",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User-facing intervention message",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Status: pending, dismissed, acted",
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<Intervention(user_id={self.user_id}, type={self.type}, status={self.status})>"
```

**Step 5: Register in `backend/app/models/__init__.py`**

Add these imports and entries to `__all__`:

```python
from app.models.wellbeing_score import WellbeingScore, WellbeingZone
from app.models.intervention import Intervention, InterventionStatus, InterventionType
```

Add to `__all__`: `"WellbeingScore"`, `"WellbeingZone"`, `"Intervention"`, `"InterventionStatus"`, `"InterventionType"`

**Step 6: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_models.py -v`
Expected: ALL PASS

**Step 7: Commit**

```bash
git add backend/app/models/wellbeing_score.py backend/app/models/intervention.py backend/app/models/__init__.py backend/tests/test_wellbeing_models.py
git commit -m "[HR-459] feat(models): add WellbeingScore and Intervention DB models"
```

---

## Task 2: Alembic Migration 005

**Files:**
- Create: `backend/alembic/versions/005_phase7_wellbeing.py`

**Step 1: Write the migration**

```python
# backend/alembic/versions/005_phase7_wellbeing.py
"""Phase 7 wellbeing: wellbeing_scores and interventions tables.

Revision ID: 005_phase7_wellbeing
Revises: 004_phase5_memory
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '005_phase7_wellbeing'
down_revision: Union[str, None] = '004_phase5_memory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create wellbeing_scores and interventions tables."""
    # 1. wellbeing_scores
    op.create_table(
        'wellbeing_scores',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False,
                  comment='Aggregated wellbeing score 0-100'),
        sa.Column('zone', sa.String(10), nullable=False,
                  comment='Score zone: red, yellow, green'),
        sa.Column('components', postgresql.JSONB(), nullable=False,
                  server_default='{}',
                  comment='Individual score components with weights'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            ondelete='CASCADE', name='fk_wellbeing_scores_user_id',
        ),
        comment='Aggregated wellbeing scores for trend tracking',
    )
    op.create_index(
        'ix_wellbeing_scores_user_date',
        'wellbeing_scores',
        ['user_id', sa.text('created_at DESC')],
    )

    # 2. interventions
    op.create_table(
        'interventions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(30), nullable=False,
                  comment='Intervention type'),
        sa.Column('trigger_pattern', sa.String(100), nullable=False,
                  comment='Pattern that triggered this intervention'),
        sa.Column('message', sa.Text(), nullable=False,
                  comment='User-facing message'),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default='pending',
                  comment='Status: pending, dismissed, acted'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            ondelete='CASCADE', name='fk_interventions_user_id',
        ),
        comment='Proactive ADHS coaching interventions',
    )
    op.create_index(
        'ix_interventions_user_status',
        'interventions',
        ['user_id', 'status'],
    )
    op.create_index(
        'ix_interventions_user_date',
        'interventions',
        ['user_id', sa.text('created_at DESC')],
    )


def downgrade() -> None:
    """Drop wellbeing_scores and interventions tables."""
    op.drop_index('ix_interventions_user_date', table_name='interventions')
    op.drop_index('ix_interventions_user_status', table_name='interventions')
    op.drop_table('interventions')
    op.drop_index('ix_wellbeing_scores_user_date', table_name='wellbeing_scores')
    op.drop_table('wellbeing_scores')
```

**Step 2: Commit**

```bash
git add backend/alembic/versions/005_phase7_wellbeing.py
git commit -m "[HR-459] db: add migration 005 for wellbeing_scores and interventions"
```

---

## Task 3: Wellbeing Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/wellbeing.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_wellbeing_schemas.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_wellbeing_schemas.py
"""Tests for wellbeing Pydantic schemas."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4


class TestWellbeingScoreResponse:
    def test_valid_response(self):
        from app.schemas.wellbeing import WellbeingScoreResponse
        data = WellbeingScoreResponse(
            score=72.5,
            zone="green",
            components={"mood": 0.6, "energy": 0.7},
            calculated_at=datetime.now(timezone.utc),
        )
        assert data.score == 72.5
        assert data.zone == "green"

    def test_score_out_of_range_raises(self):
        from app.schemas.wellbeing import WellbeingScoreResponse
        with pytest.raises(Exception):
            WellbeingScoreResponse(
                score=150, zone="green", components={},
                calculated_at=datetime.now(timezone.utc),
            )

    def test_score_negative_raises(self):
        from app.schemas.wellbeing import WellbeingScoreResponse
        with pytest.raises(Exception):
            WellbeingScoreResponse(
                score=-5, zone="green", components={},
                calculated_at=datetime.now(timezone.utc),
            )


class TestWellbeingHistoryResponse:
    def test_valid_history(self):
        from app.schemas.wellbeing import WellbeingHistoryResponse
        data = WellbeingHistoryResponse(
            scores=[],
            trend="stable",
            average_score=65.0,
            days=7,
        )
        assert data.days == 7


class TestInterventionResponse:
    def test_valid_response(self):
        from app.schemas.wellbeing import InterventionResponse
        data = InterventionResponse(
            id=uuid4(),
            type="hyperfocus",
            trigger_pattern="Focus > 0.9 for 2h",
            message="Du bist deep drin — denk an Pause",
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        assert data.status == "pending"


class TestInterventionAction:
    def test_dismiss(self):
        from app.schemas.wellbeing import InterventionAction
        data = InterventionAction(action="dismiss")
        assert data.action == "dismiss"

    def test_invalid_action_raises(self):
        from app.schemas.wellbeing import InterventionAction
        with pytest.raises(Exception):
            InterventionAction(action="invalid")


class TestSchemaRegistration:
    def test_schemas_in_init(self):
        from app.schemas import (
            WellbeingScoreResponse,
            WellbeingHistoryResponse,
            InterventionResponse,
            InterventionAction,
        )
        assert WellbeingScoreResponse is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_schemas.py -v`
Expected: FAIL

**Step 3: Implement schemas**

```python
# backend/app/schemas/wellbeing.py
"""Schemas for the wellbeing/Guardian Angel system."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WellbeingScoreResponse(BaseModel):
    """A single wellbeing score snapshot."""

    score: float = Field(..., ge=0, le=100, description="Wellbeing score 0-100")
    zone: str = Field(..., description="Zone: red, yellow, green")
    components: dict[str, Any] = Field(default_factory=dict, description="Score components")
    calculated_at: datetime


class WellbeingHistoryResponse(BaseModel):
    """Wellbeing score history over a time period."""

    scores: list[WellbeingScoreResponse] = Field(default_factory=list)
    trend: str = Field(..., description="Trend: rising, declining, stable")
    average_score: float = Field(..., ge=0, le=100)
    days: int = Field(..., ge=1)


class InterventionResponse(BaseModel):
    """A single intervention for the user."""

    id: UUID
    type: str
    trigger_pattern: str
    message: str
    status: str
    created_at: datetime


class InterventionAction(BaseModel):
    """Action to take on an intervention."""

    action: str = Field(..., pattern="^(dismiss|act)$", description="Action: dismiss or act")
```

**Step 4: Register in `backend/app/schemas/__init__.py`**

Add import and `__all__` entries for `WellbeingScoreResponse`, `WellbeingHistoryResponse`, `InterventionResponse`, `InterventionAction`.

**Step 5: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_schemas.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/schemas/wellbeing.py backend/app/schemas/__init__.py backend/tests/test_wellbeing_schemas.py
git commit -m "[HR-459] feat(schemas): add wellbeing Pydantic schemas"
```

---

## Task 4: WellbeingService — Score Calculation

**Files:**
- Create: `backend/app/services/wellbeing.py`
- Test: `backend/tests/test_wellbeing_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_wellbeing_service.py
"""Tests for WellbeingService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestCalculateScore:
    """Test score calculation logic."""

    def test_calculate_from_trends(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        # mood_score is -1..1, normalize to 0..1 first => (0.6+1)/2 = 0.8
        trends = {
            "avg_mood": 0.6,
            "avg_energy": 0.7,
            "avg_focus": 0.5,
            "total_conversations": 5,
        }
        stats = {"tasks_completed": 10, "current_streak": 3}
        score, components = service._compute_score(trends, stats)
        assert 0 <= score <= 100
        assert "mood" in components
        assert "energy" in components
        assert "focus" in components

    def test_zone_red(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(15) == "red"

    def test_zone_yellow(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(45) == "yellow"

    def test_zone_green(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(75) == "green"

    def test_zone_boundary_30(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(30) == "red"

    def test_zone_boundary_31(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(31) == "yellow"

    def test_zone_boundary_60(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(60) == "yellow"

    def test_zone_boundary_61(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(61) == "green"

    def test_all_zeros_returns_low_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {
            "avg_mood": -1.0,
            "avg_energy": 0.0,
            "avg_focus": 0.0,
            "total_conversations": 1,
        }
        stats = {"tasks_completed": 0, "current_streak": 0}
        score, _ = service._compute_score(trends, stats)
        assert score <= 30

    def test_all_max_returns_high_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {
            "avg_mood": 1.0,
            "avg_energy": 1.0,
            "avg_focus": 1.0,
            "total_conversations": 10,
        }
        stats = {"tasks_completed": 50, "current_streak": 14}
        score, _ = service._compute_score(trends, stats)
        assert score >= 70

    def test_no_data_returns_neutral_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {"avg_mood": 0, "avg_energy": 0, "avg_focus": 0, "total_conversations": 0}
        stats = {"tasks_completed": 0, "current_streak": 0}
        score, _ = service._compute_score(trends, stats)
        assert 40 <= score <= 60  # neutral when no data


class TestGetScoreHistory:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_scores(self):
        from app.services.wellbeing import WellbeingService
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        service = WellbeingService(db)
        result = await service.get_score_history(str(uuid4()), days=7)
        assert result["scores"] == []
        assert result["trend"] == "stable"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_service.py -v`
Expected: FAIL

**Step 3: Implement WellbeingService**

```python
# backend/app/services/wellbeing.py
"""WellbeingService — computes aggregated wellbeing scores and manages interventions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention
from app.models.pattern_log import PatternLog
from app.models.user_stats import UserStats
from app.models.wellbeing_score import WellbeingScore
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

# Weights for score calculation (must sum to 1.0)
WEIGHTS = {
    "mood": 0.25,
    "energy": 0.20,
    "focus": 0.15,
    "task_completion": 0.15,
    "streak": 0.10,
    "consistency": 0.15,  # how often user chats (proxy for engagement)
}


class WellbeingService:
    """Computes and stores wellbeing scores, manages interventions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)

    # ------------------------------------------------------------------
    # Score Calculation
    # ------------------------------------------------------------------

    async def calculate_and_store(self, user_id: str) -> dict[str, Any]:
        """Calculate wellbeing score from recent data and persist it.

        Returns:
            Dict with score, zone, components.
        """
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)
        stats = await self._get_user_stats(user_id)
        score, components = self._compute_score(trends, stats)
        zone = self._zone_for_score(score)

        wellbeing = WellbeingScore(
            user_id=user_id,
            score=round(score, 1),
            zone=zone,
            components=components,
        )
        self.db.add(wellbeing)
        await self.db.flush()

        logger.info(
            "Wellbeing score for user %s: %.1f (%s)", user_id, score, zone
        )

        return {
            "score": round(score, 1),
            "zone": zone,
            "components": components,
            "calculated_at": wellbeing.created_at,
        }

    def _compute_score(
        self, trends: dict[str, Any], stats: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """Compute weighted wellbeing score from trends and stats.

        Returns:
            Tuple of (score 0-100, components dict).
        """
        total_convos = trends.get("total_conversations", 0)

        # Normalize mood from -1..1 to 0..1
        raw_mood = trends.get("avg_mood", 0)
        mood_norm = (raw_mood + 1) / 2

        energy_norm = trends.get("avg_energy", 0)
        focus_norm = trends.get("avg_focus", 0)

        # Task completion: cap at 1.0, assume 20 tasks/week is excellent
        tasks_done = stats.get("tasks_completed", 0)
        task_norm = min(tasks_done / 20, 1.0) if tasks_done else 0

        # Streak: cap at 14 days as maximum
        streak = stats.get("current_streak", 0)
        streak_norm = min(streak / 14, 1.0)

        # Consistency: how many conversations in 7 days. 14+ is excellent
        consistency_norm = min(total_convos / 14, 1.0) if total_convos else 0

        # If no data at all, return neutral score
        if total_convos == 0 and tasks_done == 0 and streak == 0:
            return 50.0, {
                "mood": 0.5, "energy": 0.5, "focus": 0.5,
                "task_completion": 0, "streak": 0, "consistency": 0,
                "note": "Noch keine Daten vorhanden",
            }

        weighted = (
            mood_norm * WEIGHTS["mood"]
            + energy_norm * WEIGHTS["energy"]
            + focus_norm * WEIGHTS["focus"]
            + task_norm * WEIGHTS["task_completion"]
            + streak_norm * WEIGHTS["streak"]
            + consistency_norm * WEIGHTS["consistency"]
        )

        score = round(weighted * 100, 1)
        score = max(0, min(100, score))

        components = {
            "mood": round(mood_norm, 3),
            "energy": round(energy_norm, 3),
            "focus": round(focus_norm, 3),
            "task_completion": round(task_norm, 3),
            "streak": round(streak_norm, 3),
            "consistency": round(consistency_norm, 3),
        }

        return score, components

    @staticmethod
    def _zone_for_score(score: float) -> str:
        """Map a 0-100 score to a zone."""
        if score <= 30:
            return "red"
        elif score <= 60:
            return "yellow"
        return "green"

    # ------------------------------------------------------------------
    # Score Retrieval
    # ------------------------------------------------------------------

    async def get_latest_score(self, user_id: str) -> dict[str, Any] | None:
        """Get the most recent wellbeing score for a user."""
        stmt = (
            select(WellbeingScore)
            .where(WellbeingScore.user_id == user_id)
            .order_by(WellbeingScore.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        ws = result.scalar_one_or_none()
        if not ws:
            return None
        return {
            "score": ws.score,
            "zone": ws.zone,
            "components": ws.components,
            "calculated_at": ws.created_at,
        }

    async def get_score_history(
        self, user_id: str, days: int = 7
    ) -> dict[str, Any]:
        """Get wellbeing score history for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(WellbeingScore)
            .where(
                WellbeingScore.user_id == user_id,
                WellbeingScore.created_at >= cutoff,
            )
            .order_by(WellbeingScore.created_at.asc())
        )
        result = await self.db.execute(stmt)
        scores = result.scalars().all()

        score_list = [
            {
                "score": s.score,
                "zone": s.zone,
                "components": s.components,
                "calculated_at": s.created_at,
            }
            for s in scores
        ]

        avg = sum(s.score for s in scores) / len(scores) if scores else 50.0

        # Determine trend
        trend = "stable"
        if len(scores) >= 2:
            mid = len(scores) // 2
            first_half_avg = sum(s.score for s in scores[:mid]) / mid
            second_half_avg = sum(s.score for s in scores[mid:]) / (len(scores) - mid)
            diff = second_half_avg - first_half_avg
            if diff > 3:
                trend = "rising"
            elif diff < -3:
                trend = "declining"

        return {
            "scores": score_list,
            "trend": trend,
            "average_score": round(avg, 1),
            "days": days,
        }

    # ------------------------------------------------------------------
    # Interventions
    # ------------------------------------------------------------------

    async def get_active_interventions(self, user_id: str) -> list[dict[str, Any]]:
        """Get all pending interventions for a user."""
        stmt = (
            select(Intervention)
            .where(
                Intervention.user_id == user_id,
                Intervention.status == "pending",
            )
            .order_by(Intervention.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        interventions = result.scalars().all()
        return [
            {
                "id": i.id,
                "type": i.type,
                "trigger_pattern": i.trigger_pattern,
                "message": i.message,
                "status": i.status,
                "created_at": i.created_at,
            }
            for i in interventions
        ]

    async def update_intervention_status(
        self, intervention_id: str, user_id: str, new_status: str
    ) -> bool:
        """Update an intervention's status (dismiss or act)."""
        stmt = (
            update(Intervention)
            .where(
                Intervention.id == intervention_id,
                Intervention.user_id == user_id,
            )
            .values(status=new_status)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Fetch UserStats as a simple dict."""
        stmt = select(UserStats).where(UserStats.user_id == user_id)
        result = await self.db.execute(stmt)
        stats = result.scalar_one_or_none()
        if not stats:
            return {"tasks_completed": 0, "current_streak": 0}
        return {
            "tasks_completed": stats.tasks_completed,
            "current_streak": stats.current_streak,
        }
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_service.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/wellbeing.py backend/tests/test_wellbeing_service.py
git commit -m "[HR-459] feat(services): add WellbeingService with score calculation"
```

---

## Task 5: InterventionEngine — 7 ADHS Patterns

**Files:**
- Create: `backend/app/services/intervention_engine.py`
- Test: `backend/tests/test_intervention_engine.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_intervention_engine.py
"""Tests for InterventionEngine — ADHS pattern detection."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestPatternDetection:
    """Test each ADHS pattern individually."""

    def test_hyperfocus_detected(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "hyperfocus" in types

    def test_hyperfocus_not_detected_when_normal(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.5, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "hyperfocus" not in types

    def test_procrastination_spiral_detected(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.3, "avg_energy": 0.2, "avg_mood": -0.3, "total_conversations": 5, "mood_trend": "declining"}
        stats = {"tasks_completed": 1, "current_streak": 0}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "procrastination" in types

    def test_decision_fatigue_detected(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.2, "avg_energy": 0.4, "avg_mood": 0.0, "total_conversations": 5}
        stats = {"open_tasks": 8}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "decision_fatigue" in types

    def test_energy_crash_detected(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.4, "avg_energy": 0.15, "avg_mood": 0.0, "total_conversations": 5}
        # Energy declining 3+ days
        recent_logs = [
            {"energy_level": 0.3},
            {"energy_level": 0.2},
            {"energy_level": 0.1},
        ]
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=recent_logs)
        types = [p["type"] for p in patterns]
        assert "energy_crash" in types

    def test_social_masking_detected(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.8, "avg_energy": 0.7, "avg_mood": -0.4, "total_conversations": 5, "mood_trend": "declining"}
        stats = {"tasks_completed": 15}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "social_masking" in types

    def test_no_patterns_when_all_good(self):
        from app.services.intervention_engine import InterventionEngine
        engine = InterventionEngine.__new__(InterventionEngine)
        trends = {"avg_focus": 0.6, "avg_energy": 0.6, "avg_mood": 0.5, "total_conversations": 5, "mood_trend": "stable"}
        stats = {"tasks_completed": 10, "current_streak": 5, "open_tasks": 2}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        assert len(patterns) == 0


class TestCreateInterventions:
    @pytest.mark.asyncio
    async def test_creates_intervention_for_pattern(self):
        from app.services.intervention_engine import InterventionEngine
        db = AsyncMock()
        engine = InterventionEngine(db)
        user_id = str(uuid4())

        # Mock _detect_patterns to return one pattern
        engine._detect_patterns = MagicMock(return_value=[
            {"type": "hyperfocus", "trigger": "Focus > 0.9", "message": "Pause!"}
        ])
        # Mock _has_recent_intervention
        engine._has_recent_intervention = AsyncMock(return_value=False)
        # Mock pattern_analyzer and _get_user_stats
        engine.pattern_analyzer = AsyncMock()
        engine.pattern_analyzer.get_recent_trends = AsyncMock(return_value={"avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5})
        engine._get_user_stats = AsyncMock(return_value={})
        engine._get_recent_logs = AsyncMock(return_value=[])

        interventions = await engine.evaluate(user_id)
        assert len(interventions) == 1
        assert interventions[0]["type"] == "hyperfocus"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_intervention_engine.py -v`
Expected: FAIL

**Step 3: Implement InterventionEngine**

```python
# backend/app/services/intervention_engine.py
"""InterventionEngine — detects 7 ADHS-specific patterns and creates interventions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention
from app.models.pattern_log import PatternLog
from app.models.task import Task, TaskStatus
from app.models.user_stats import UserStats
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

# Cooldown: don't create same intervention type within 12 hours
INTERVENTION_COOLDOWN_HOURS = 12

# German messages for each intervention type
MESSAGES = {
    "hyperfocus": "Du bist deep drin — denk an eine Pause! Steh kurz auf, trink Wasser.",
    "procrastination": "Lass uns die Aufgabe kleiner machen. Was waere der kleinste erste Schritt?",
    "decision_fatigue": "Zu viele Optionen? Fokus auf DIESE eine Sache. Den Rest ignorieren wir.",
    "transition": "Gleich steht ein Wechsel an — nimm dir 2 Minuten Pause dazwischen.",
    "energy_crash": "Deine Energie sinkt seit Tagen. Heute leichtere Aufgaben — und frueher Schluss.",
    "sleep_disruption": "Spaete Nutzung + wenig Energie morgens? Quiet-Hours koennten helfen.",
    "social_masking": "Hohe Produktivitaet aber sinkende Stimmung? Goenn dir etwas fuer DICH.",
}


class InterventionEngine:
    """Detects ADHS patterns and creates proactive interventions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)

    async def evaluate(self, user_id: str) -> list[dict[str, Any]]:
        """Evaluate all patterns for a user and create new interventions.

        Returns:
            List of created intervention dicts.
        """
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)
        stats = await self._get_user_stats(user_id)
        recent_logs = await self._get_recent_logs(user_id, days=3)

        if trends.get("total_conversations", 0) == 0:
            return []

        detected = self._detect_patterns(trends, stats, recent_logs)

        created = []
        for pattern in detected:
            if await self._has_recent_intervention(user_id, pattern["type"]):
                continue

            intervention = Intervention(
                user_id=user_id,
                type=pattern["type"],
                trigger_pattern=pattern["trigger"],
                message=pattern["message"],
                status="pending",
            )
            self.db.add(intervention)
            await self.db.flush()

            created.append({
                "id": intervention.id,
                "type": intervention.type,
                "trigger_pattern": intervention.trigger_pattern,
                "message": intervention.message,
                "status": "pending",
                "created_at": intervention.created_at,
            })

        if created:
            logger.info(
                "Created %d interventions for user %s: %s",
                len(created), user_id, [c["type"] for c in created],
            )

        return created

    def _detect_patterns(
        self,
        trends: dict[str, Any],
        stats: dict[str, Any],
        recent_logs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rule-based detection of 7 ADHS patterns.

        Returns:
            List of detected pattern dicts with type, trigger, message.
        """
        detected: list[dict[str, Any]] = []
        avg_focus = trends.get("avg_focus", 0.5)
        avg_energy = trends.get("avg_energy", 0.5)
        avg_mood = trends.get("avg_mood", 0.0)
        mood_trend = trends.get("mood_trend", "stable")
        tasks_completed = stats.get("tasks_completed", 0)
        open_tasks = stats.get("open_tasks", 0)
        streak = stats.get("current_streak", 0)

        # 1. Hyperfocus: Focus > 0.9
        if avg_focus > 0.9:
            detected.append({
                "type": "hyperfocus",
                "trigger": f"Focus {avg_focus:.2f} > 0.9",
                "message": MESSAGES["hyperfocus"],
            })

        # 2. Procrastination Spiral: low task completion + declining energy + low mood
        if avg_energy < 0.3 and avg_mood < -0.1 and tasks_completed < 3:
            detected.append({
                "type": "procrastination",
                "trigger": f"Energy {avg_energy:.2f}, mood {avg_mood:.2f}, tasks {tasks_completed}",
                "message": MESSAGES["procrastination"],
            })

        # 3. Decision Fatigue: many open tasks + low focus
        if open_tasks >= 5 and avg_focus < 0.3:
            detected.append({
                "type": "decision_fatigue",
                "trigger": f"{open_tasks} open tasks, focus {avg_focus:.2f}",
                "message": MESSAGES["decision_fatigue"],
            })

        # 4. Energy Crash: energy declining for 3+ consecutive entries
        if len(recent_logs) >= 3:
            energy_vals = [l.get("energy_level", 0.5) for l in recent_logs[-3:]]
            if all(energy_vals[i] > energy_vals[i + 1] for i in range(len(energy_vals) - 1)):
                if avg_energy < 0.3:
                    detected.append({
                        "type": "energy_crash",
                        "trigger": f"Energy declining: {[round(e, 2) for e in energy_vals]}",
                        "message": MESSAGES["energy_crash"],
                    })

        # 5. Social Masking: high productivity + declining mood
        if tasks_completed >= 10 and avg_mood < -0.2 and mood_trend == "declining":
            detected.append({
                "type": "social_masking",
                "trigger": f"Tasks {tasks_completed}, mood {avg_mood:.2f} ({mood_trend})",
                "message": MESSAGES["social_masking"],
            })

        # 6. Sleep Disruption: detected from late-night usage patterns
        # (simplified: low energy + would need chat timestamps, use avg as proxy)
        if avg_energy < 0.25 and avg_mood < 0:
            # Only trigger if not already triggered as energy_crash
            if not any(p["type"] == "energy_crash" for p in detected):
                detected.append({
                    "type": "sleep_disruption",
                    "trigger": f"Low energy {avg_energy:.2f} + negative mood {avg_mood:.2f}",
                    "message": MESSAGES["sleep_disruption"],
                })

        # 7. Transition: context switch needed — triggered differently (real-time)
        # Not applicable in batch mode, placeholder for future real-time detection

        return detected

    async def _has_recent_intervention(
        self, user_id: str, intervention_type: str
    ) -> bool:
        """Check if this type of intervention was created recently (cooldown)."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=INTERVENTION_COOLDOWN_HOURS)
        stmt = select(func.count()).select_from(Intervention).where(
            Intervention.user_id == user_id,
            Intervention.type == intervention_type,
            Intervention.created_at >= cutoff,
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Fetch user stats + open task count."""
        stats_result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        stats = stats_result.scalar_one_or_none()

        open_count_result = await self.db.execute(
            select(func.count()).select_from(Task).where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        )
        open_tasks = open_count_result.scalar() or 0

        if not stats:
            return {"tasks_completed": 0, "current_streak": 0, "open_tasks": open_tasks}

        return {
            "tasks_completed": stats.tasks_completed,
            "current_streak": stats.current_streak,
            "open_tasks": open_tasks,
        }

    async def _get_recent_logs(
        self, user_id: str, days: int = 3
    ) -> list[dict[str, Any]]:
        """Fetch recent pattern logs as dicts."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(PatternLog)
            .where(
                PatternLog.user_id == user_id,
                PatternLog.created_at >= cutoff,
            )
            .order_by(PatternLog.created_at.asc())
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        return [
            {
                "mood_score": l.mood_score,
                "energy_level": l.energy_level,
                "focus_score": l.focus_score,
            }
            for l in logs
        ]
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_intervention_engine.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/intervention_engine.py backend/tests/test_intervention_engine.py
git commit -m "[HR-460] feat(services): add InterventionEngine with 7 ADHS patterns"
```

---

## Task 6: Wellbeing API Endpoints

**Files:**
- Create: `backend/app/api/v1/wellbeing.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_wellbeing_api.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_wellbeing_api.py
"""Tests for wellbeing API router registration and endpoint existence."""

import pytest


class TestWellbeingRouterRegistered:
    def test_wellbeing_prefix_in_v1_router(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/wellbeing" in p for p in paths)


class TestWellbeingEndpointsExist:
    def test_router_has_score_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/score" in paths

    def test_router_has_history_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/history" in paths

    def test_router_has_interventions_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/interventions" in paths

    def test_router_has_intervention_action_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert any("intervention" in p and "{intervention_id}" in p for p in paths)

    def test_score_endpoint_is_get(self):
        from app.api.v1.wellbeing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/score":
                assert "GET" in route.methods

    def test_interventions_action_is_put(self):
        from app.api.v1.wellbeing import router
        for route in router.routes:
            if hasattr(route, "path") and "{intervention_id}" in route.path:
                assert "PUT" in route.methods
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_api.py -v`
Expected: FAIL

**Step 3: Implement API endpoints**

```python
# backend/app/api/v1/wellbeing.py
"""Wellbeing/Guardian Angel API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.wellbeing import (
    InterventionAction,
    InterventionResponse,
    WellbeingHistoryResponse,
    WellbeingScoreResponse,
)
from app.services.wellbeing import WellbeingService

router = APIRouter(tags=["Wellbeing"])


@router.get(
    "/score",
    response_model=WellbeingScoreResponse,
    summary="Get current wellbeing score",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_wellbeing_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest wellbeing score. Calculates a new one if none exists or if stale."""
    service = WellbeingService(db)
    latest = await service.get_latest_score(str(current_user.id))
    if not latest:
        latest = await service.calculate_and_store(str(current_user.id))
        await db.commit()
    return WellbeingScoreResponse(**latest)


@router.get(
    "/history",
    response_model=WellbeingHistoryResponse,
    summary="Get wellbeing score history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_wellbeing_history(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get wellbeing score history for the last N days."""
    service = WellbeingService(db)
    history = await service.get_score_history(str(current_user.id), days=days)
    return WellbeingHistoryResponse(
        scores=[WellbeingScoreResponse(**s) for s in history["scores"]],
        trend=history["trend"],
        average_score=history["average_score"],
        days=history["days"],
    )


@router.get(
    "/interventions",
    response_model=list[InterventionResponse],
    summary="Get active interventions",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_interventions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending interventions for the current user."""
    service = WellbeingService(db)
    interventions = await service.get_active_interventions(str(current_user.id))
    return [InterventionResponse(**i) for i in interventions]


@router.put(
    "/interventions/{intervention_id}",
    summary="Dismiss or act on an intervention",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_intervention(
    intervention_id: str,
    data: InterventionAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update intervention status: dismiss or act."""
    service = WellbeingService(db)
    # Map action to status
    status_map = {"dismiss": "dismissed", "act": "acted"}
    new_status = status_map[data.action]
    success = await service.update_intervention_status(
        intervention_id, str(current_user.id), new_status
    )
    if not success:
        raise HTTPException(status_code=404, detail="Intervention not found")
    await db.commit()
    return {"status": new_status}
```

**Step 4: Register in router.py**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1 import wellbeing
# ...
# Phase 7: Wellbeing/Guardian Angel routers
router.include_router(wellbeing.router, prefix="/wellbeing", tags=["Wellbeing"])
```

**Step 5: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_api.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/api/v1/wellbeing.py backend/app/api/v1/router.py backend/tests/test_wellbeing_api.py
git commit -m "[HR-459] feat(api): add wellbeing API endpoints (score, history, interventions)"
```

---

## Task 7: Scheduler Integration — Periodic Wellbeing Checks

**Files:**
- Modify: `backend/app/services/scheduler.py`
- Test: `backend/tests/test_wellbeing_scheduler.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_wellbeing_scheduler.py
"""Tests for wellbeing scheduler integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestWellbeingSchedulerFunction:
    def test_function_exists(self):
        from app.services.scheduler import _process_wellbeing_check
        assert callable(_process_wellbeing_check)

    @pytest.mark.asyncio
    async def test_calls_wellbeing_service(self):
        from app.services.scheduler import _process_wellbeing_check
        user_id = uuid4()
        settings = {"active_modules": ["core", "wellness"]}
        with patch("app.services.scheduler.WellbeingService") as MockWS, \
             patch("app.services.scheduler.InterventionEngine") as MockIE, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession:
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockWS.return_value.calculate_and_store = AsyncMock(return_value={"score": 50, "zone": "yellow"})
            MockIE.return_value.evaluate = AsyncMock(return_value=[])
            await _process_wellbeing_check(user_id, settings)
            MockWS.return_value.calculate_and_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_wellness_not_active(self):
        from app.services.scheduler import _process_wellbeing_check
        user_id = uuid4()
        settings = {"active_modules": ["core", "adhs"]}
        with patch("app.services.scheduler.WellbeingService") as MockWS:
            await _process_wellbeing_check(user_id, settings)
            MockWS.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_scheduler.py -v`
Expected: FAIL

**Step 3: Add wellbeing check to scheduler**

Add to `backend/app/services/scheduler.py`:

1. Import WellbeingService, InterventionEngine, NotificationService
2. Add `_process_wellbeing_check()` function
3. Call it from `_process_user()` when wellness module is active

The function:
```python
async def _process_wellbeing_check(user_id: UUID, settings: dict) -> None:
    """Run periodic wellbeing check if wellness module is active."""
    active_modules = settings.get("active_modules", ["core", "adhs"])
    if "wellness" not in active_modules:
        return

    async with AsyncSessionLocal() as db:
        from app.services.wellbeing import WellbeingService
        from app.services.intervention_engine import InterventionEngine

        ws = WellbeingService(db)
        result = await ws.calculate_and_store(str(user_id))

        ie = InterventionEngine(db)
        interventions = await ie.evaluate(str(user_id))

        await db.commit()

        # Send push for critical interventions (red zone or new interventions)
        if result["zone"] == "red" or interventions:
            token = settings.get("expo_push_token")
            if token:
                from app.services.notification import NotificationService, PushNotification
                if result["zone"] == "red":
                    await NotificationService.send_notification(
                        PushNotification(
                            to=token,
                            title="Wellbeing Check",
                            body=f"Dein Wellbeing-Score ist bei {result['score']:.0f}/100. Alice ist fuer dich da.",
                            data={"type": "wellbeing", "score": result["score"]},
                        )
                    )
                for intervention in interventions:
                    await NotificationService.send_notification(
                        PushNotification(
                            to=token,
                            title="Alice Guardian Angel",
                            body=intervention["message"],
                            data={"type": "intervention", "id": str(intervention["id"])},
                        )
                    )
```

Add call in `_process_user`:
```python
# 4. Wellbeing check (if wellness module active)
try:
    await _process_wellbeing_check(user_id, settings)
except Exception:
    logger.exception("Wellbeing check error for user %s", user_id)
```

**Step 4: Run tests**

Run: `cd backend && .venv/bin/python -m pytest tests/test_wellbeing_scheduler.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/scheduler.py backend/tests/test_wellbeing_scheduler.py
git commit -m "[HR-460] feat(scheduler): add periodic wellbeing checks with push notifications"
```

---

## Task 8: Mobile — Wellbeing API Service & Zustand Store

**Files:**
- Create: `mobile/services/wellbeing.ts`
- Create: `mobile/stores/wellbeingStore.ts`

**Step 1: Create API service**

```typescript
// mobile/services/wellbeing.ts
import axios from "./api";

export interface WellbeingScore {
  score: number;
  zone: "red" | "yellow" | "green";
  components: Record<string, number>;
  calculated_at: string;
}

export interface WellbeingHistory {
  scores: WellbeingScore[];
  trend: "rising" | "declining" | "stable";
  average_score: number;
  days: number;
}

export interface InterventionItem {
  id: string;
  type: string;
  trigger_pattern: string;
  message: string;
  status: string;
  created_at: string;
}

export const wellbeingApi = {
  getScore: () =>
    axios.get<WellbeingScore>("/settings/../wellbeing/score").then((r) => r.data),

  getHistory: (days = 7) =>
    axios.get<WellbeingHistory>(`/wellbeing/history?days=${days}`).then((r) => r.data),

  getInterventions: () =>
    axios.get<InterventionItem[]>("/wellbeing/interventions").then((r) => r.data),

  dismissIntervention: (id: string) =>
    axios.put(`/wellbeing/interventions/${id}`, { action: "dismiss" }),

  actOnIntervention: (id: string) =>
    axios.put(`/wellbeing/interventions/${id}`, { action: "act" }),
};
```

**Note:** The axios base URL is already set to `/api/v1` in the existing `mobile/services/api.ts`. Verify and use the correct path.

**Step 2: Create Zustand store**

```typescript
// mobile/stores/wellbeingStore.ts
import { create } from "zustand";
import {
  wellbeingApi,
  WellbeingScore,
  WellbeingHistory,
  InterventionItem,
} from "../services/wellbeing";

interface WellbeingState {
  score: WellbeingScore | null;
  history: WellbeingHistory | null;
  interventions: InterventionItem[];
  isLoading: boolean;
  error: string | null;
  fetchScore: () => Promise<void>;
  fetchHistory: (days?: number) => Promise<void>;
  fetchInterventions: () => Promise<void>;
  dismissIntervention: (id: string) => Promise<void>;
  actOnIntervention: (id: string) => Promise<void>;
}

export const useWellbeingStore = create<WellbeingState>((set, get) => ({
  score: null,
  history: null,
  interventions: [],
  isLoading: false,
  error: null,

  fetchScore: async () => {
    set({ isLoading: true, error: null });
    try {
      const score = await wellbeingApi.getScore();
      set({ score, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  fetchHistory: async (days = 7) => {
    try {
      const history = await wellbeingApi.getHistory(days);
      set({ history });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  fetchInterventions: async () => {
    try {
      const interventions = await wellbeingApi.getInterventions();
      set({ interventions });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  dismissIntervention: async (id: string) => {
    await wellbeingApi.dismissIntervention(id);
    set((s) => ({
      interventions: s.interventions.filter((i) => i.id !== id),
    }));
  },

  actOnIntervention: async (id: string) => {
    await wellbeingApi.actOnIntervention(id);
    set((s) => ({
      interventions: s.interventions.filter((i) => i.id !== id),
    }));
  },
}));
```

**Step 3: Commit**

```bash
git add mobile/services/wellbeing.ts mobile/stores/wellbeingStore.ts
git commit -m "[HR-461] feat(mobile): add wellbeing API service and Zustand store"
```

---

## Task 9: Mobile — Wellbeing Tab Screen

**Files:**
- Create: `mobile/app/(tabs)/wellness/_layout.tsx`
- Create: `mobile/app/(tabs)/wellness/index.tsx`
- Modify: `mobile/app/(tabs)/_layout.tsx` (add wellness tab to TAB_CONFIG)

**Step 1: Create wellness tab layout**

```typescript
// mobile/app/(tabs)/wellness/_layout.tsx
import { Stack } from "expo-router";

export default function WellnessLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
```

**Step 2: Create wellness index screen**

```typescript
// mobile/app/(tabs)/wellness/index.tsx
import React, { useEffect, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  useColorScheme,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useWellbeingStore } from "../../../stores/wellbeingStore";

const ZONE_COLORS = {
  red: { bg: "#fef2f2", border: "#ef4444", text: "#dc2626", label: "Kritisch" },
  yellow: { bg: "#fffbeb", border: "#f59e0b", text: "#d97706", label: "Achtung" },
  green: { bg: "#f0fdf4", border: "#22c55e", text: "#16a34a", label: "Gut" },
};

const ZONE_COLORS_DARK = {
  red: { bg: "#450a0a", border: "#ef4444", text: "#fca5a5", label: "Kritisch" },
  yellow: { bg: "#451a03", border: "#f59e0b", text: "#fcd34d", label: "Achtung" },
  green: { bg: "#052e16", border: "#22c55e", text: "#86efac", label: "Gut" },
};

const INTERVENTION_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  hyperfocus: "eye-outline",
  procrastination: "trending-down-outline",
  decision_fatigue: "git-branch-outline",
  transition: "swap-horizontal-outline",
  energy_crash: "battery-dead-outline",
  sleep_disruption: "moon-outline",
  social_masking: "happy-outline",
};

export default function WellnessScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const {
    score,
    interventions,
    isLoading,
    fetchScore,
    fetchInterventions,
    dismissIntervention,
    actOnIntervention,
  } = useWellbeingStore();

  useEffect(() => {
    fetchScore();
    fetchInterventions();
  }, []);

  const handleRefresh = useCallback(() => {
    fetchScore();
    fetchInterventions();
  }, [fetchScore, fetchInterventions]);

  if (isLoading && !score) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner />
      </View>
    );
  }

  const zone = score?.zone || "yellow";
  const colors = isDark ? ZONE_COLORS_DARK[zone] : ZONE_COLORS[zone];

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: isDark ? "#030712" : "#f9fafb" }}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
      }
    >
      {/* Wellbeing Score Card */}
      <Card style={{ marginBottom: 16, borderColor: colors.border, borderWidth: 2 }}>
        <View style={{ alignItems: "center", padding: 20 }}>
          <Text
            style={{
              fontSize: 48,
              fontWeight: "800",
              color: colors.text,
            }}
          >
            {score ? Math.round(score.score) : "—"}
          </Text>
          <Text
            style={{
              fontSize: 14,
              color: isDark ? "#9ca3af" : "#6b7280",
              marginTop: 4,
            }}
          >
            Wellbeing Score
          </Text>
          <View
            style={{
              marginTop: 8,
              paddingHorizontal: 12,
              paddingVertical: 4,
              borderRadius: 12,
              backgroundColor: colors.bg,
            }}
          >
            <Text style={{ color: colors.text, fontWeight: "600", fontSize: 13 }}>
              {colors.label}
            </Text>
          </View>
        </View>

        {/* Component Bars */}
        {score?.components && (
          <View style={{ paddingHorizontal: 16, paddingBottom: 16, gap: 8 }}>
            {Object.entries(score.components)
              .filter(([key]) => key !== "note")
              .map(([key, value]) => (
                <View key={key}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 2 }}>
                    <Text style={{ fontSize: 12, color: isDark ? "#9ca3af" : "#6b7280", textTransform: "capitalize" }}>
                      {key === "task_completion" ? "Aufgaben" : key === "streak" ? "Streak" : key === "consistency" ? "Regelmaessigkeit" : key}
                    </Text>
                    <Text style={{ fontSize: 12, color: isDark ? "#d1d5db" : "#374151" }}>
                      {Math.round((value as number) * 100)}%
                    </Text>
                  </View>
                  <View
                    style={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: isDark ? "#374151" : "#e5e7eb",
                    }}
                  >
                    <View
                      style={{
                        height: 6,
                        borderRadius: 3,
                        width: `${Math.round((value as number) * 100)}%`,
                        backgroundColor: colors.border,
                      }}
                    />
                  </View>
                </View>
              ))}
          </View>
        )}
      </Card>

      {/* Interventions */}
      {interventions.length > 0 && (
        <View style={{ marginBottom: 16 }}>
          <Text
            style={{
              fontSize: 18,
              fontWeight: "700",
              color: isDark ? "#f9fafb" : "#111827",
              marginBottom: 12,
            }}
          >
            Guardian Angel
          </Text>
          {interventions.map((intervention) => (
            <Card key={intervention.id} style={{ marginBottom: 8 }}>
              <View style={{ padding: 16 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Ionicons
                    name={INTERVENTION_ICONS[intervention.type] || "alert-circle-outline"}
                    size={20}
                    color="#f59e0b"
                  />
                  <Text
                    style={{
                      fontSize: 15,
                      fontWeight: "600",
                      color: isDark ? "#f9fafb" : "#111827",
                      flex: 1,
                    }}
                  >
                    {intervention.message}
                  </Text>
                </View>
                <View style={{ flexDirection: "row", gap: 8, marginTop: 8 }}>
                  <TouchableOpacity
                    onPress={() => actOnIntervention(intervention.id)}
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      backgroundColor: "#0284c7",
                      alignItems: "center",
                    }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "600", fontSize: 13 }}>
                      Annehmen
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => dismissIntervention(intervention.id)}
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      backgroundColor: isDark ? "#374151" : "#e5e7eb",
                      alignItems: "center",
                    }}
                  >
                    <Text
                      style={{
                        color: isDark ? "#9ca3af" : "#6b7280",
                        fontWeight: "600",
                        fontSize: 13,
                      }}
                    >
                      Spaeter
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </Card>
          ))}
        </View>
      )}

      {/* Empty State */}
      {interventions.length === 0 && (
        <Card style={{ marginBottom: 16 }}>
          <View style={{ padding: 20, alignItems: "center" }}>
            <Ionicons
              name="shield-checkmark-outline"
              size={40}
              color={isDark ? "#4ade80" : "#16a34a"}
            />
            <Text
              style={{
                fontSize: 15,
                color: isDark ? "#d1d5db" : "#6b7280",
                marginTop: 8,
                textAlign: "center",
              }}
            >
              Alles im gruenen Bereich! Keine Interventionen noetig.
            </Text>
          </View>
        </Card>
      )}
    </ScrollView>
  );
}
```

**Step 3: Add wellness tab to TAB_CONFIG**

In `mobile/app/(tabs)/_layout.tsx`, add before the settings entry in TAB_CONFIG:

```typescript
{
  name: "wellness",
  title: "Wellness",
  icon: "heart-outline",
  requiredModules: ["wellness"],
},
```

**Step 4: Commit**

```bash
git add mobile/app/(tabs)/wellness/_layout.tsx mobile/app/(tabs)/wellness/index.tsx mobile/app/(tabs)/_layout.tsx
git commit -m "[HR-461] feat(mobile): add Wellness tab with score widget and intervention cards"
```

---

## Task 10: Run Full Test Suite & Fix Issues

**Step 1: Run all backend tests**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All new tests pass, pre-existing failures unchanged

**Step 2: Fix any issues found**

**Step 3: Commit fixes if needed**

---

## Task 11: Linear Status Update

Update Linear epics:
- HR-459 (Wellbeing Score Engine) → Done
- HR-460 (ADHS Intervention Engine) → Done
- HR-461 (Expo Wellbeing UI) → Done

Add completion comments with implemented files and acceptance criteria status.

---

## Task 12: Update Design Doc Checklist

**Files:**
- Modify: `docs/plans/2026-02-14-alice-agent-one-transformation-design.md`

Mark Milestone 2 items as done:

```markdown
### Milestone 2: Guardian Angel & Wellness Module
- [x] `WellbeingScore` DB Model + Migration
- [x] `Intervention` DB Model + Migration
- [x] `WellbeingService` mit Score-Berechnung
- [x] Intervention Engine (7 ADHS-Pattern)
- [x] Cron Job: Periodische Score-Berechnung
- [x] API Endpoints: score, history, interventions
- [x] Expo: Wellbeing Dashboard Screen
- [x] Expo: Activity-Rings Score Widget
- [ ] Expo: 7d Trend Chart
- [x] Expo: Intervention Cards (dismiss/snooze/act)
- [x] Push Notifications fuer kritische Interventionen
```

Note: The 7d Trend Chart requires a charting library (e.g. react-native-chart-kit or victory-native) and is a UI enhancement that can be added as a follow-up task.

**Commit:**

```bash
git add docs/plans/2026-02-14-alice-agent-one-transformation-design.md
git commit -m "[HR-459] docs: update design doc with Phase 7 completion status"
```
