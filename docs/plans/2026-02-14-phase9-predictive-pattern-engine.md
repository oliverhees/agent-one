# Phase 9: Predictive Pattern Engine — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Predict ADHS behavioral patterns (energy crashes, procrastination spirals, hyperfocus traps) before they happen, using rule-based sliding-window analysis with optional Graphiti knowledge graph enrichment.

**Architecture:** Approach B — Deterministic rule-based predictions on PatternLog/WellbeingScore data with 7d+30d sliding windows. Each of the 7 existing InterventionType patterns gets a dedicated prediction rule that calculates a confidence score (0.0-1.0). GraphitiClient optionally enriches predictions with contextual facts from the knowledge graph, with graceful degradation when FalkorDB is unavailable.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, Expo SDK 52, TypeScript, Zustand

---

### Task 1: PredictedPattern DB Model

**Files:**
- Create: `backend/app/models/predicted_pattern.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py` (add relationship)
- Test: `backend/tests/test_prediction_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_models.py
"""Tests for PredictedPattern model."""
import pytest
from datetime import datetime, timedelta, timezone

from app.models.predicted_pattern import PredictedPattern, PredictionStatus


class TestPredictedPatternModel:
    """Test PredictedPattern model creation and defaults."""

    def test_prediction_status_enum_values(self):
        assert PredictionStatus.ACTIVE == "active"
        assert PredictionStatus.CONFIRMED == "confirmed"
        assert PredictionStatus.AVOIDED == "avoided"
        assert PredictionStatus.EXPIRED == "expired"

    @pytest.mark.asyncio
    async def test_create_predicted_pattern(self, db_session, test_user):
        prediction = PredictedPattern(
            user_id=test_user.id,
            pattern_type="energy_crash",
            confidence=0.78,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=24),
            time_horizon="24h",
            trigger_factors={"energy_trend": "declining", "avg_energy": 0.32},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(prediction)
        await db_session.flush()

        assert prediction.id is not None
        assert prediction.pattern_type == "energy_crash"
        assert prediction.confidence == 0.78
        assert prediction.time_horizon == "24h"
        assert prediction.status == "active"
        assert prediction.resolved_at is None

    @pytest.mark.asyncio
    async def test_prediction_user_relationship(self, db_session, test_user):
        prediction = PredictedPattern(
            user_id=test_user.id,
            pattern_type="procrastination",
            confidence=0.65,
            predicted_for=datetime.now(timezone.utc) + timedelta(days=3),
            time_horizon="3d",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(prediction)
        await db_session.flush()

        assert prediction.user is not None
        assert prediction.user.id == test_user.id

    @pytest.mark.asyncio
    async def test_prediction_repr(self, db_session, test_user):
        prediction = PredictedPattern(
            user_id=test_user.id,
            pattern_type="hyperfocus",
            confidence=0.85,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=12),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(prediction)
        await db_session.flush()

        repr_str = repr(prediction)
        assert "PredictedPattern" in repr_str
        assert "hyperfocus" in repr_str
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_models.py -v`
Expected: FAIL with import errors (module doesn't exist yet)

**Step 3: Write the PredictedPattern model**

```python
# backend/app/models/predicted_pattern.py
"""PredictedPattern model for behavioral pattern predictions."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class PredictionStatus(str, enum.Enum):
    """Status of a prediction."""

    ACTIVE = "active"
    CONFIRMED = "confirmed"
    AVOIDED = "avoided"
    EXPIRED = "expired"


class PredictedPattern(BaseModel):
    """Predicted behavioral pattern for a user."""

    __tablename__ = "predicted_patterns"
    __table_args__ = (
        Index("ix_predicted_patterns_user_status", "user_id", "status"),
        Index("ix_predicted_patterns_user_predicted", "user_id", "predicted_for"),
        {"comment": "ADHS behavioral pattern predictions"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this prediction belongs to",
    )

    pattern_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="One of 7 InterventionType values",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence score 0.0-1.0",
    )

    predicted_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the pattern is predicted to occur",
    )

    time_horizon: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Prediction horizon: 24h, 3d, 7d",
    )

    trigger_factors: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Metrics that triggered this prediction",
    )

    graphiti_context: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Optional enrichment from knowledge graph",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PredictionStatus.ACTIVE,
        comment="Status: active, confirmed, avoided, expired",
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When the prediction was resolved",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="predicted_patterns",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PredictedPattern(id={self.id}, type={self.pattern_type}, "
            f"confidence={self.confidence}, status={self.status})>"
        )
```

**Step 4: Update `backend/app/models/__init__.py`** — Add imports:

```python
from app.models.predicted_pattern import PredictedPattern, PredictionStatus
```

And add to `__all__`: `"PredictedPattern"`, `"PredictionStatus"`

**Step 5: Update `backend/app/models/user.py`** — Add relationship:

```python
# In TYPE_CHECKING block:
from app.models.predicted_pattern import PredictedPattern

# In User class:
predicted_patterns: Mapped[list["PredictedPattern"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

**Step 6: Run test to verify it passes**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_models.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add backend/app/models/predicted_pattern.py backend/app/models/__init__.py backend/app/models/user.py backend/tests/test_prediction_models.py
git commit -m "feat(prediction): add PredictedPattern model with PredictionStatus enum"
```

---

### Task 2: Alembic Migration 007

**Files:**
- Create: `backend/alembic/versions/007_phase9_predicted_patterns.py`
- Test: Run migration up and down

**Step 1: Create the migration**

```python
# backend/alembic/versions/007_phase9_predicted_patterns.py
"""Phase 9: predicted_patterns table.

Revision ID: 007
Revises: 006
Create Date: 2026-02-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predicted_patterns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pattern_type", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("predicted_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_horizon", sa.String(10), nullable=False),
        sa.Column("trigger_factors", JSONB, nullable=False, server_default="{}"),
        sa.Column("graphiti_context", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment="ADHS behavioral pattern predictions",
    )

    op.create_index("ix_predicted_patterns_user_status", "predicted_patterns", ["user_id", "status"])
    op.create_index("ix_predicted_patterns_user_predicted", "predicted_patterns", ["user_id", "predicted_for"])


def downgrade() -> None:
    op.drop_index("ix_predicted_patterns_user_predicted", table_name="predicted_patterns")
    op.drop_index("ix_predicted_patterns_user_status", table_name="predicted_patterns")
    op.drop_table("predicted_patterns")
```

**Step 2: Run migration**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && alembic upgrade head`
Expected: SUCCESS

**Step 3: Verify downgrade works**

Run: `alembic downgrade 006 && alembic upgrade head`

**Step 4: Commit**

```bash
git add backend/alembic/versions/007_phase9_predicted_patterns.py
git commit -m "db(prediction): add migration 007 for predicted_patterns table"
```

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/prediction.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_prediction_schemas.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_schemas.py
"""Tests for prediction Pydantic schemas."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas.prediction import (
    PredictionResponse,
    PredictionListResponse,
    PredictionResolveRequest,
)


class TestPredictionSchemas:
    def test_prediction_response_serialization(self):
        data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "pattern_type": "energy_crash",
            "confidence": 0.78,
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": {"energy_trend": "declining"},
            "graphiti_context": {},
            "status": "active",
            "resolved_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        resp = PredictionResponse(**data)
        assert resp.pattern_type == "energy_crash"
        assert resp.confidence == 0.78
        assert resp.status == "active"

    def test_prediction_list_response(self):
        predictions = []
        for i in range(3):
            predictions.append({
                "id": str(uuid4()),
                "user_id": str(uuid4()),
                "pattern_type": "procrastination",
                "confidence": 0.6 + i * 0.1,
                "predicted_for": datetime.now(timezone.utc),
                "time_horizon": "3d",
                "trigger_factors": {},
                "graphiti_context": {},
                "status": "active",
                "resolved_at": None,
                "created_at": datetime.now(timezone.utc),
            })

        resp = PredictionListResponse(
            predictions=[PredictionResponse(**p) for p in predictions],
            total=3,
        )
        assert resp.total == 3
        assert len(resp.predictions) == 3

    def test_prediction_resolve_request_valid(self):
        req = PredictionResolveRequest(status="confirmed")
        assert req.status == "confirmed"

    def test_prediction_resolve_request_avoided(self):
        req = PredictionResolveRequest(status="avoided")
        assert req.status == "avoided"

    def test_prediction_resolve_request_invalid_status(self):
        with pytest.raises(Exception):
            PredictionResolveRequest(status="active")
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_schemas.py -v`

**Step 3: Write the schemas**

```python
# backend/app/schemas/prediction.py
"""Pydantic schemas for prediction endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response schema for a single prediction."""

    id: str
    user_id: str
    pattern_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    predicted_for: datetime
    time_horizon: str
    trigger_factors: dict[str, Any]
    graphiti_context: dict[str, Any]
    status: str
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    """Response schema for a list of predictions."""

    predictions: list[PredictionResponse]
    total: int


class PredictionResolveRequest(BaseModel):
    """Request to resolve a prediction."""

    status: Literal["confirmed", "avoided"]
```

**Step 4: Update `backend/app/schemas/__init__.py`** — Add imports:

```python
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionResolveRequest,
    PredictionResponse,
)
```

And add to `__all__`: `"PredictionResponse"`, `"PredictionListResponse"`, `"PredictionResolveRequest"`

**Step 5: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_schemas.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add backend/app/schemas/prediction.py backend/app/schemas/__init__.py backend/tests/test_prediction_schemas.py
git commit -m "feat(prediction): add Pydantic schemas for prediction endpoints"
```

---

### Task 4: Extended PatternAnalyzer — Multi-Metric Trends

**Files:**
- Modify: `backend/app/services/pattern_analyzer.py`
- Test: `backend/tests/test_prediction_analyzer.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_analyzer.py
"""Tests for extended PatternAnalyzer with multi-metric trends."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.pattern_log import PatternLog
from app.services.pattern_analyzer import PatternAnalyzer


class TestMultiMetricTrends:
    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_returns_all_trends(self, db_session, test_user):
        """Should return trend direction for energy and focus, not just mood."""
        now = datetime.now(timezone.utc)
        # Create declining energy pattern: high early, low recently
        for i in range(6):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.5,
                energy_level=0.8 - (i * 0.1),  # 0.8 → 0.3
                focus_score=0.3 + (i * 0.1),   # 0.3 → 0.8 (rising)
            )
            db_session.add(log)
            await db_session.flush()
            # Manually set created_at for time ordering
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        analyzer = PatternAnalyzer(db_session)
        trends = await analyzer.get_multi_metric_trends(str(test_user.id), days=7)

        assert "energy_trend" in trends
        assert "focus_trend" in trends
        assert "mood_trend" in trends
        assert trends["energy_trend"] == "declining"
        assert trends["focus_trend"] == "rising"

    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_empty_user(self, db_session, test_user):
        """Should return neutral defaults for user with no logs."""
        analyzer = PatternAnalyzer(db_session)
        trends = await analyzer.get_multi_metric_trends(str(test_user.id), days=7)

        assert trends["total_conversations"] == 0
        assert trends["mood_trend"] == "stable"
        assert trends["energy_trend"] == "stable"
        assert trends["focus_trend"] == "stable"

    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_30d(self, db_session, test_user):
        """Should support 30-day window."""
        now = datetime.now(timezone.utc)
        for i in range(10):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.2,
                energy_level=0.5,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=25 - i)
            await db_session.flush()

        analyzer = PatternAnalyzer(db_session)
        trends = await analyzer.get_multi_metric_trends(str(test_user.id), days=30)
        assert trends["total_conversations"] == 10
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_analyzer.py -v`
Expected: FAIL (method doesn't exist yet)

**Step 3: Add `get_multi_metric_trends` to PatternAnalyzer**

Add this method to `backend/app/services/pattern_analyzer.py`:

```python
async def get_multi_metric_trends(
    self, user_id: str | UUID, days: int = 7
) -> dict[str, Any]:
    """Get trends for ALL three metrics (mood, energy, focus)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        func.avg(PatternLog.mood_score).label("avg_mood"),
        func.avg(PatternLog.energy_level).label("avg_energy"),
        func.avg(PatternLog.focus_score).label("avg_focus"),
        func.count(PatternLog.id).label("total"),
        func.min(PatternLog.mood_score).label("min_mood"),
        func.max(PatternLog.mood_score).label("max_mood"),
        func.min(PatternLog.energy_level).label("min_energy"),
        func.max(PatternLog.energy_level).label("max_energy"),
        func.min(PatternLog.focus_score).label("min_focus"),
        func.max(PatternLog.focus_score).label("max_focus"),
    ).where(
        PatternLog.user_id == str(user_id),
        PatternLog.created_at >= cutoff,
    )

    result = (await self.db.execute(stmt)).one()

    mood_trend = await self._calculate_trend(user_id, days, "mood_score")
    energy_trend = await self._calculate_trend(user_id, days, "energy_level")
    focus_trend = await self._calculate_trend(user_id, days, "focus_score")

    return {
        "avg_mood": round(float(result.avg_mood or 0), 2),
        "avg_energy": round(float(result.avg_energy or 0), 2),
        "avg_focus": round(float(result.avg_focus or 0), 2),
        "total_conversations": int(result.total or 0),
        "min_mood": round(float(result.min_mood or 0), 2),
        "max_mood": round(float(result.max_mood or 0), 2),
        "min_energy": round(float(result.min_energy or 0), 2),
        "max_energy": round(float(result.max_energy or 0), 2),
        "min_focus": round(float(result.min_focus or 0), 2),
        "max_focus": round(float(result.max_focus or 0), 2),
        "mood_trend": mood_trend,
        "energy_trend": energy_trend,
        "focus_trend": focus_trend,
    }
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_analyzer.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/services/pattern_analyzer.py backend/tests/test_prediction_analyzer.py
git commit -m "feat(prediction): extend PatternAnalyzer with multi-metric trend analysis"
```

---

### Task 5: PredictionEngine Service

**Files:**
- Create: `backend/app/services/prediction_engine.py`
- Test: `backend/tests/test_prediction_engine.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_engine.py
"""Tests for PredictionEngine service."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.pattern_log import PatternLog
from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.services.prediction_engine import PredictionEngine


class TestPredictionEngine:
    @pytest.mark.asyncio
    async def test_predict_returns_empty_when_no_data(self, db_session, test_user):
        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))
        assert results == []

    @pytest.mark.asyncio
    async def test_predict_energy_crash(self, db_session, test_user):
        """Declining energy over 7d should predict energy crash."""
        now = datetime.now(timezone.utc)
        # Create declining energy: first half high, second half low
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.7,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.25,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=2 - i)
            await db_session.flush()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        types = [r["pattern_type"] for r in results]
        assert "energy_crash" in types

    @pytest.mark.asyncio
    async def test_predict_respects_confidence_threshold(self, db_session, test_user):
        """Predictions below 0.6 confidence should not be returned."""
        now = datetime.now(timezone.utc)
        # Mild data — not enough for high confidence
        for i in range(3):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.3,
                energy_level=0.5,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=3 - i)
            await db_session.flush()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        for r in results:
            assert r["confidence"] >= 0.6

    @pytest.mark.asyncio
    async def test_predict_cooldown_prevents_duplicates(self, db_session, test_user):
        """Should not create duplicate prediction within 24h cooldown."""
        # Create existing active prediction
        existing = PredictedPattern(
            user_id=test_user.id,
            pattern_type="energy_crash",
            confidence=0.75,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=12),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(existing)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.7,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.2,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=2 - i)
            await db_session.flush()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        energy_crash_count = sum(1 for r in results if r["pattern_type"] == "energy_crash")
        assert energy_crash_count == 0  # blocked by cooldown

    @pytest.mark.asyncio
    async def test_predict_with_graphiti_enrichment(self, db_session, test_user):
        """Should add graphiti_context when client is available."""
        now = datetime.now(timezone.utc)
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.7,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.2,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=2 - i)
            await db_session.flush()

        mock_graphiti = MagicMock()
        mock_graphiti.enabled = True
        mock_graphiti.search = AsyncMock(return_value=[
            {"fact": "User hat abends oft Energieprobleme", "valid_at": None}
        ])

        engine = PredictionEngine(db_session, graphiti_client=mock_graphiti)
        results = await engine.predict(str(test_user.id))

        enriched = [r for r in results if r.get("graphiti_context", {}).get("related_facts")]
        # If any prediction was created, it should have been enriched
        if results:
            assert len(enriched) > 0

    @pytest.mark.asyncio
    async def test_predict_graceful_without_graphiti(self, db_session, test_user):
        """Should work fine without Graphiti client."""
        now = datetime.now(timezone.utc)
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.7,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.2,
                focus_score=0.5,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=2 - i)
            await db_session.flush()

        engine = PredictionEngine(db_session, graphiti_client=None)
        results = await engine.predict(str(test_user.id))

        for r in results:
            assert r["graphiti_context"] == {}

    @pytest.mark.asyncio
    async def test_expire_old_predictions(self, db_session, test_user):
        """Should expire predictions whose predicted_for is in the past."""
        old = PredictedPattern(
            user_id=test_user.id,
            pattern_type="hyperfocus",
            confidence=0.8,
            predicted_for=datetime.now(timezone.utc) - timedelta(hours=2),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(old)
        await db_session.flush()

        engine = PredictionEngine(db_session)
        expired_count = await engine.expire_old_predictions(str(test_user.id))
        assert expired_count == 1

        await db_session.refresh(old)
        assert old.status == PredictionStatus.EXPIRED
```

**Step 2: Run test to verify it fails**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_engine.py -v`

**Step 3: Write PredictionEngine service**

```python
# backend/app/services/prediction_engine.py
"""PredictionEngine — predicts ADHS behavioral patterns before they happen."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.pattern_log import PatternLog
from app.models.task import Task, TaskStatus
from app.models.user_stats import UserStats
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

PREDICTION_COOLDOWN_HOURS = 24
CONFIDENCE_THRESHOLD = 0.6


class PredictionEngine:
    """Predicts ADHS behavioral patterns using rule-based analysis with optional Graphiti enrichment."""

    def __init__(self, db: AsyncSession, graphiti_client: Any = None) -> None:
        self.db = db
        self.analyzer = PatternAnalyzer(db)
        self.graphiti = graphiti_client

    async def predict(self, user_id: str) -> list[dict[str, Any]]:
        """Run all prediction rules and store results."""
        trends_7d = await self.analyzer.get_multi_metric_trends(user_id, days=7)
        trends_30d = await self.analyzer.get_multi_metric_trends(user_id, days=30)

        if trends_7d["total_conversations"] == 0:
            return []

        stats = await self._get_user_stats(user_id)
        recent_logs = await self._get_recent_logs(user_id, days=3)

        candidates: list[dict[str, Any]] = []

        for rule in [
            self._predict_energy_crash,
            self._predict_procrastination,
            self._predict_hyperfocus,
            self._predict_decision_fatigue,
            self._predict_sleep_disruption,
            self._predict_social_masking,
        ]:
            result = rule(trends_7d, trends_30d, stats, recent_logs)
            if result and result["confidence"] >= CONFIDENCE_THRESHOLD:
                candidates.append(result)

        created: list[dict[str, Any]] = []
        for candidate in candidates:
            if await self._has_recent_prediction(user_id, candidate["pattern_type"]):
                continue

            if self.graphiti and getattr(self.graphiti, "enabled", False):
                candidate["graphiti_context"] = await self._enrich_with_graphiti(
                    user_id, candidate["pattern_type"]
                )
            else:
                candidate["graphiti_context"] = {}

            prediction = PredictedPattern(
                user_id=user_id,
                pattern_type=candidate["pattern_type"],
                confidence=candidate["confidence"],
                predicted_for=candidate["predicted_for"],
                time_horizon=candidate["time_horizon"],
                trigger_factors=candidate["trigger_factors"],
                graphiti_context=candidate["graphiti_context"],
                status=PredictionStatus.ACTIVE,
            )
            self.db.add(prediction)
            await self.db.flush()

            created.append({
                "id": str(prediction.id),
                "pattern_type": prediction.pattern_type,
                "confidence": prediction.confidence,
                "predicted_for": prediction.predicted_for.isoformat(),
                "time_horizon": prediction.time_horizon,
                "trigger_factors": prediction.trigger_factors,
                "graphiti_context": prediction.graphiti_context,
                "status": prediction.status,
            })

        if created:
            logger.info(
                "Created %d predictions for user %s: %s",
                len(created), user_id, [c["pattern_type"] for c in created],
            )

        return created

    async def expire_old_predictions(self, user_id: str) -> int:
        """Expire active predictions whose predicted_for is in the past."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(PredictedPattern)
            .where(
                PredictedPattern.user_id == user_id,
                PredictedPattern.status == PredictionStatus.ACTIVE,
                PredictedPattern.predicted_for < now,
            )
        )
        result = await self.db.execute(stmt)
        expired = result.scalars().all()

        for p in expired:
            p.status = PredictionStatus.EXPIRED
            p.resolved_at = now

        return len(expired)

    # ------------------------------------------------------------------
    # Prediction Rules
    # ------------------------------------------------------------------

    def _predict_energy_crash(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["energy_trend"] == "declining":
            confidence += 0.35
            factors["energy_trend_7d"] = "declining"
        if t7["avg_energy"] < 0.4:
            confidence += 0.25
            factors["avg_energy_7d"] = t7["avg_energy"]
        if t7["focus_trend"] == "declining":
            confidence += 0.15
            factors["focus_trend_7d"] = "declining"
        if t30["avg_energy"] > t7["avg_energy"] + 0.15:
            confidence += 0.25
            factors["energy_drop_vs_30d"] = round(t30["avg_energy"] - t7["avg_energy"], 2)

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "energy_crash",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_procrastination(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_energy"] < 0.35:
            confidence += 0.25
            factors["low_energy"] = t7["avg_energy"]
        if t7["avg_mood"] < -0.1:
            confidence += 0.2
            factors["negative_mood"] = t7["avg_mood"]
        if stats.get("tasks_completed", 0) < 3:
            confidence += 0.2
            factors["low_task_completion"] = stats.get("tasks_completed", 0)
        if t7["mood_trend"] == "declining":
            confidence += 0.2
            factors["mood_declining"] = True
        if t30["avg_energy"] > t7["avg_energy"] + 0.1:
            confidence += 0.15
            factors["energy_below_baseline"] = True

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "procrastination",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=3),
            "time_horizon": "3d",
            "trigger_factors": factors,
        }

    def _predict_hyperfocus(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_focus"] > 0.85:
            confidence += 0.35
            factors["high_focus"] = t7["avg_focus"]
        if t7["focus_trend"] == "rising":
            confidence += 0.25
            factors["focus_rising"] = True
        if t7["avg_energy"] < 0.4:
            confidence += 0.2
            factors["energy_depleting"] = t7["avg_energy"]
        if t7["avg_focus"] > t30["avg_focus"] + 0.15:
            confidence += 0.2
            factors["focus_above_baseline"] = round(t7["avg_focus"] - t30["avg_focus"], 2)

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "hyperfocus",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_decision_fatigue(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        open_tasks = stats.get("open_tasks", 0)
        if open_tasks >= 5:
            confidence += 0.3
            factors["many_open_tasks"] = open_tasks
        if t7["avg_focus"] < 0.35:
            confidence += 0.25
            factors["low_focus"] = t7["avg_focus"]
        if t7["focus_trend"] == "declining":
            confidence += 0.2
            factors["focus_declining"] = True
        if open_tasks >= 8:
            confidence += 0.15
            factors["task_overload"] = open_tasks
        if t7["avg_mood"] < 0:
            confidence += 0.1
            factors["negative_mood"] = t7["avg_mood"]

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "decision_fatigue",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_sleep_disruption(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_energy"] < 0.3:
            confidence += 0.3
            factors["very_low_energy"] = t7["avg_energy"]
        if t7["avg_mood"] < -0.1:
            confidence += 0.2
            factors["negative_mood"] = t7["avg_mood"]
        if t7["energy_trend"] == "declining":
            confidence += 0.2
            factors["energy_declining"] = True
        if t30["avg_energy"] > t7["avg_energy"] + 0.2:
            confidence += 0.2
            factors["significant_energy_drop"] = round(t30["avg_energy"] - t7["avg_energy"], 2)
        if t7["avg_focus"] < 0.3:
            confidence += 0.1
            factors["low_focus_too"] = t7["avg_focus"]

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "sleep_disruption",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=3),
            "time_horizon": "3d",
            "trigger_factors": factors,
        }

    def _predict_social_masking(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        tasks_completed = stats.get("tasks_completed", 0)
        if tasks_completed >= 8:
            confidence += 0.3
            factors["high_productivity"] = tasks_completed
        if t7["avg_mood"] < -0.1:
            confidence += 0.25
            factors["declining_mood"] = t7["avg_mood"]
        if t7["mood_trend"] == "declining":
            confidence += 0.25
            factors["mood_trend_declining"] = True
        if t7["avg_focus"] > 0.7:
            confidence += 0.1
            factors["high_focus_masking"] = t7["avg_focus"]
        if t30["avg_mood"] > t7["avg_mood"] + 0.15:
            confidence += 0.1
            factors["mood_below_baseline"] = True

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "social_masking",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=7),
            "time_horizon": "7d",
            "trigger_factors": factors,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _enrich_with_graphiti(self, user_id: str, pattern_type: str) -> dict[str, Any]:
        """Query Graphiti for contextual facts related to a pattern type."""
        try:
            facts = await self.graphiti.search(
                query=f"ADHS {pattern_type} Verhaltensmuster",
                user_id=user_id,
                num_results=5,
            )
            return {
                "related_facts": facts,
                "enrichment_time": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.warning("Graphiti enrichment failed for %s: %s", pattern_type, exc)
            return {}

    async def _has_recent_prediction(self, user_id: str, pattern_type: str) -> bool:
        """Check if an active prediction of this type exists within cooldown."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=PREDICTION_COOLDOWN_HOURS)
        stmt = (
            select(func.count())
            .select_from(PredictedPattern)
            .where(
                PredictedPattern.user_id == user_id,
                PredictedPattern.pattern_type == pattern_type,
                PredictedPattern.status == PredictionStatus.ACTIVE,
                PredictedPattern.created_at >= cutoff,
            )
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        stats_result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        stats = stats_result.scalar_one_or_none()

        open_count_result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
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

    async def _get_recent_logs(self, user_id: str, days: int = 3) -> list[dict[str, Any]]:
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
        return [
            {
                "mood_score": log.mood_score,
                "energy_level": log.energy_level,
                "focus_score": log.focus_score,
            }
            for log in result.scalars().all()
        ]
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_engine.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add backend/app/services/prediction_engine.py backend/tests/test_prediction_engine.py
git commit -m "feat(prediction): add PredictionEngine with 6 ADHS prediction rules and Graphiti enrichment"
```

---

### Task 6: Prediction API Endpoints

**Files:**
- Create: `backend/app/api/v1/prediction.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_prediction_api.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_api.py
"""Tests for prediction API endpoints."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.predicted_pattern import PredictedPattern, PredictionStatus


class TestPredictionAPI:
    @pytest.mark.asyncio
    async def test_get_active_predictions(self, client, auth_headers, db_session, test_user):
        p = PredictedPattern(
            user_id=test_user.id,
            pattern_type="energy_crash",
            confidence=0.78,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=12),
            time_horizon="24h",
            trigger_factors={"test": True},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(p)
        await db_session.commit()

        response = await client.get("/api/v1/predictions/active", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(p["pattern_type"] == "energy_crash" for p in data["predictions"])

    @pytest.mark.asyncio
    async def test_get_prediction_history(self, client, auth_headers, db_session, test_user):
        for status in [PredictionStatus.ACTIVE, PredictionStatus.CONFIRMED, PredictionStatus.EXPIRED]:
            p = PredictedPattern(
                user_id=test_user.id,
                pattern_type="procrastination",
                confidence=0.7,
                predicted_for=datetime.now(timezone.utc),
                time_horizon="3d",
                trigger_factors={},
                graphiti_context={},
                status=status,
            )
            db_session.add(p)
        await db_session.commit()

        response = await client.get("/api/v1/predictions/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_resolve_prediction_confirmed(self, client, auth_headers, db_session, test_user):
        p = PredictedPattern(
            user_id=test_user.id,
            pattern_type="hyperfocus",
            confidence=0.85,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=6),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(p)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/predictions/{p.id}/resolve",
            json={"status": "confirmed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_resolve_prediction_avoided(self, client, auth_headers, db_session, test_user):
        p = PredictedPattern(
            user_id=test_user.id,
            pattern_type="decision_fatigue",
            confidence=0.72,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=6),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        db_session.add(p)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/predictions/{p.id}/resolve",
            json={"status": "avoided"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "avoided"

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_prediction(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/predictions/{fake_id}/resolve",
            json={"status": "confirmed"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_predictions_manually(self, client, auth_headers):
        response = await client.post("/api/v1/predictions/run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
```

**Step 2: Run test to verify it fails**

**Step 3: Write the API endpoints**

```python
# backend/app/api/v1/prediction.py
"""Prediction API endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.user import User
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionResolveRequest,
    PredictionResponse,
)
from app.services.prediction_engine import PredictionEngine
from app.services.graphiti_client import get_graphiti_client

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/active", response_model=PredictionListResponse)
async def get_active_predictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active predictions for the current user."""
    stmt = (
        select(PredictedPattern)
        .where(
            PredictedPattern.user_id == current_user.id,
            PredictedPattern.status == PredictionStatus.ACTIVE,
        )
        .order_by(PredictedPattern.confidence.desc())
    )
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    return PredictionListResponse(
        predictions=[PredictionResponse.model_validate(p) for p in predictions],
        total=len(predictions),
    )


@router.get("/history", response_model=PredictionListResponse)
async def get_prediction_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prediction history for the current user."""
    count_stmt = (
        select(func.count())
        .select_from(PredictedPattern)
        .where(PredictedPattern.user_id == current_user.id)
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(PredictedPattern)
        .where(PredictedPattern.user_id == current_user.id)
        .order_by(PredictedPattern.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    return PredictionListResponse(
        predictions=[PredictionResponse.model_validate(p) for p in predictions],
        total=total,
    )


@router.post("/{prediction_id}/resolve", response_model=PredictionResponse)
async def resolve_prediction(
    prediction_id: UUID,
    body: PredictionResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve a prediction as confirmed or avoided."""
    stmt = select(PredictedPattern).where(
        PredictedPattern.id == prediction_id,
        PredictedPattern.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    prediction = result.scalar_one_or_none()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    prediction.status = body.status
    prediction.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prediction)

    return PredictionResponse.model_validate(prediction)


@router.post("/run")
async def run_predictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger prediction engine for the current user."""
    graphiti = get_graphiti_client()
    engine = PredictionEngine(db, graphiti_client=graphiti)

    expired = await engine.expire_old_predictions(str(current_user.id))
    predictions = await engine.predict(str(current_user.id))
    await db.commit()

    return {
        "predictions": predictions,
        "expired_count": expired,
    }
```

**Step 4: Update `backend/app/api/v1/router.py`** — Add:

```python
from app.api.v1.prediction import router as prediction_router
api_router.include_router(prediction_router)
```

**Step 5: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_api.py -v`
Expected: PASS (6 tests)

**Step 6: Commit**

```bash
git add backend/app/api/v1/prediction.py backend/app/api/v1/router.py backend/tests/test_prediction_api.py
git commit -m "feat(prediction): add prediction API endpoints (active, history, resolve, run)"
```

---

### Task 7: Scheduler Integration

**Files:**
- Modify: `backend/app/services/scheduler.py`
- Test: `backend/tests/test_prediction_scheduler.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_prediction_scheduler.py
"""Tests for prediction scheduler integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestPredictionScheduler:
    @pytest.mark.asyncio
    async def test_process_predictions_skipped_without_module(self):
        from app.services.scheduler import _process_predictions
        settings = {"active_modules": ["core", "adhs"]}
        await _process_predictions(uuid4(), settings)
        # Should return without error — wellness module not active

    @pytest.mark.asyncio
    async def test_process_predictions_runs_with_wellness(self):
        from app.services.scheduler import _process_predictions
        settings = {"active_modules": ["core", "adhs", "wellness"]}

        with patch("app.services.scheduler.PredictionEngine") as MockEngine:
            mock_instance = MagicMock()
            mock_instance.expire_old_predictions = AsyncMock(return_value=0)
            mock_instance.predict = AsyncMock(return_value=[])
            MockEngine.return_value = mock_instance

            await _process_predictions(uuid4(), settings)
            mock_instance.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_predictions_sends_push_for_high_confidence(self):
        from app.services.scheduler import _process_predictions
        settings = {
            "active_modules": ["core", "adhs", "wellness"],
            "expo_push_token": "ExponentPushToken[test]",
        }

        with patch("app.services.scheduler.PredictionEngine") as MockEngine, \
             patch("app.services.scheduler.NotificationService") as MockNotif:
            mock_instance = MagicMock()
            mock_instance.expire_old_predictions = AsyncMock(return_value=0)
            mock_instance.predict = AsyncMock(return_value=[{
                "id": str(uuid4()),
                "pattern_type": "energy_crash",
                "confidence": 0.85,
                "predicted_for": "2026-02-15T10:00:00Z",
                "time_horizon": "24h",
                "trigger_factors": {},
                "graphiti_context": {},
                "status": "active",
            }])
            MockEngine.return_value = mock_instance
            MockNotif.send_notification = AsyncMock()

            await _process_predictions(uuid4(), settings)
            MockNotif.send_notification.assert_called_once()
```

**Step 2: Run test to verify it fails**

**Step 3: Add `_process_predictions` to scheduler**

Add to `backend/app/services/scheduler.py`:

- Import: `from app.services.prediction_engine import PredictionEngine`
- Add `_process_predictions` function
- Call it from `_process_user` as step 6

```python
# Add after _process_morning_briefing call in _process_user:
    # 6. Prediction engine (if wellness module active)
    try:
        await _process_predictions(user_id, settings)
    except Exception:
        logger.exception("Prediction engine error for user %s", user_id)


async def _process_predictions(user_id: UUID, settings: dict) -> None:
    """Run prediction engine if wellness module is active."""
    active_modules = settings.get("active_modules", ["core", "adhs"])
    if "wellness" not in active_modules:
        return

    async with AsyncSessionLocal() as db:
        from app.services.graphiti_client import get_graphiti_client
        graphiti = get_graphiti_client()
        engine = PredictionEngine(db, graphiti_client=graphiti)

        await engine.expire_old_predictions(str(user_id))
        predictions = await engine.predict(str(user_id))
        await db.commit()

        # Push notification for high-confidence predictions
        token = settings.get("expo_push_token")
        if token and predictions:
            for pred in predictions:
                if pred["confidence"] >= 0.75:
                    PATTERN_LABELS = {
                        "energy_crash": "Energie-Einbruch",
                        "procrastination": "Prokrastinations-Spirale",
                        "hyperfocus": "Hyperfokus-Falle",
                        "decision_fatigue": "Entscheidungsmuedigkeit",
                        "sleep_disruption": "Schlafproblem",
                        "social_masking": "Social Masking",
                    }
                    label = PATTERN_LABELS.get(pred["pattern_type"], pred["pattern_type"])
                    await NotificationService.send_notification(
                        PushNotification(
                            to=token,
                            title="Pattern-Vorhersage",
                            body=f"Alice sieht einen moeglichen {label} in den naechsten {pred['time_horizon']}.",
                            data={"type": "prediction", "id": pred["id"]},
                        )
                    )
```

**Step 4: Run tests**

Run: `cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend && python -m pytest tests/test_prediction_scheduler.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/services/scheduler.py backend/tests/test_prediction_scheduler.py
git commit -m "feat(prediction): integrate PredictionEngine into scheduler with push notifications"
```

---

### Task 8: Mobile API Service & Zustand Store

**Files:**
- Create: `mobile/services/predictions.ts`
- Create: `mobile/stores/predictionStore.ts`

**Step 1: Create API service**

```typescript
// mobile/services/predictions.ts
import api from './api';

export interface Prediction {
  id: string;
  user_id: string;
  pattern_type: string;
  confidence: number;
  predicted_for: string;
  time_horizon: string;
  trigger_factors: Record<string, unknown>;
  graphiti_context: Record<string, unknown>;
  status: string;
  resolved_at: string | null;
  created_at: string;
}

export interface PredictionListResponse {
  predictions: Prediction[];
  total: number;
}

export const predictionsApi = {
  getActive: () => api.get<PredictionListResponse>('/predictions/active'),

  getHistory: (limit = 20, offset = 0) =>
    api.get<PredictionListResponse>(`/predictions/history?limit=${limit}&offset=${offset}`),

  resolve: (id: string, status: 'confirmed' | 'avoided') =>
    api.post<Prediction>(`/predictions/${id}/resolve`, { status }),

  runManually: () =>
    api.post<{ predictions: Prediction[]; expired_count: number }>('/predictions/run'),
};
```

**Step 2: Create Zustand store**

```typescript
// mobile/stores/predictionStore.ts
import { create } from 'zustand';
import { predictionsApi, Prediction } from '../services/predictions';

interface PredictionState {
  activePredictions: Prediction[];
  history: Prediction[];
  historyTotal: number;
  isLoading: boolean;
  error: string | null;
  fetchActive: () => Promise<void>;
  fetchHistory: (limit?: number, offset?: number) => Promise<void>;
  resolve: (id: string, status: 'confirmed' | 'avoided') => Promise<void>;
  runManually: () => Promise<void>;
}

export const usePredictionStore = create<PredictionState>((set, get) => ({
  activePredictions: [],
  history: [],
  historyTotal: 0,
  isLoading: false,
  error: null,

  fetchActive: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await predictionsApi.getActive();
      set({ activePredictions: res.data.predictions, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Fehler beim Laden', isLoading: false });
    }
  },

  fetchHistory: async (limit = 20, offset = 0) => {
    set({ isLoading: true, error: null });
    try {
      const res = await predictionsApi.getHistory(limit, offset);
      set({
        history: res.data.predictions,
        historyTotal: res.data.total,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message || 'Fehler beim Laden', isLoading: false });
    }
  },

  resolve: async (id, status) => {
    try {
      await predictionsApi.resolve(id, status);
      const { activePredictions } = get();
      set({
        activePredictions: activePredictions.filter((p) => p.id !== id),
      });
    } catch (err: any) {
      set({ error: err.message || 'Fehler beim Aktualisieren' });
    }
  },

  runManually: async () => {
    set({ isLoading: true, error: null });
    try {
      await predictionsApi.runManually();
      await get().fetchActive();
    } catch (err: any) {
      set({ error: err.message || 'Fehler', isLoading: false });
    }
  },
}));
```

**Step 3: Commit**

```bash
git add mobile/services/predictions.ts mobile/stores/predictionStore.ts
git commit -m "feat(prediction): add mobile API service and Zustand store for predictions"
```

---

### Task 9: Mobile Pattern Insights Screen

**Files:**
- Create: `mobile/app/(tabs)/insights/_layout.tsx`
- Create: `mobile/app/(tabs)/insights/index.tsx`
- Modify: `mobile/app/(tabs)/_layout.tsx` (add Insights tab)

**Step 1: Create layout**

```typescript
// mobile/app/(tabs)/insights/_layout.tsx
import { Stack } from 'expo-router';

export default function InsightsLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
    </Stack>
  );
}
```

**Step 2: Create Insights Screen**

The screen should have:
- Header "Pattern Insights"
- Active Predictions section with cards showing: pattern type (German label), confidence badge (color-coded), time horizon, trigger factors summary, "Eingetreten" / "Vermieden" action buttons
- History section below with resolved predictions
- Pull-to-refresh to reload
- Empty state when no predictions

Pattern type labels in German:
```
energy_crash → "Energie-Einbruch"
procrastination → "Prokrastinations-Spirale"
hyperfocus → "Hyperfokus-Falle"
decision_fatigue → "Entscheidungsmuedigkeit"
sleep_disruption → "Schlafproblem"
social_masking → "Social Masking"
```

Confidence colors:
- >= 0.8 → red (#EF4444)
- >= 0.6 → orange (#F59E0B)
- < 0.6 → green (#10B981)

**Step 3: Add tab to `_layout.tsx`**

Add "Insights" tab with `Ionicons` icon `analytics-outline` to the TAB_CONFIG in `mobile/app/(tabs)/_layout.tsx`.

**Step 4: Commit**

```bash
git add mobile/app/(tabs)/insights/ mobile/app/(tabs)/_layout.tsx
git commit -m "feat(prediction): add Pattern Insights screen with prediction cards"
```

---

### Task 10: Full Test Suite Run

**Files:** None (validation only)

**Step 1: Run all Phase 9 backend tests**

```bash
cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/backend
python -m pytest tests/test_prediction_models.py tests/test_prediction_schemas.py tests/test_prediction_analyzer.py tests/test_prediction_engine.py tests/test_prediction_api.py tests/test_prediction_scheduler.py -v
```

Expected: ALL PASS

**Step 2: Run full backend test suite**

```bash
python -m pytest tests/ -v --ignore=tests/test_graphiti_client.py --tb=short
```

Verify: No regressions from existing tests

**Step 3: Verify TypeScript compiles**

```bash
cd /media/oliver/Platte\ 2\ \(Netac\)1/alice-adhs-coach/mobile
npx tsc --noEmit
```

**Step 4: Update design doc checklist**

Update `docs/plans/2026-02-14-alice-agent-one-transformation-design.md` Milestone 4 checklist items to `[x]`.

**Step 5: Final commit**

```bash
git add -A
git commit -m "test(prediction): validate Phase 9 full test suite — all passing"
```
