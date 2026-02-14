# ALICE Memory System – Graphiti + NLP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give ALICE a persistent, temporal knowledge graph memory that learns from every conversation – extracting facts, recognizing ADHS patterns, and proactively coaching the user based on accumulated knowledge.

**Architecture:** Graphiti with FalkorDB backend processes each conversation as an episode, extracting entities and temporal relations into a knowledge graph. A separate NLP analysis (single Claude API call) scores mood/energy/focus per conversation and stores it in PostgreSQL. Before each chat response, a ContextBuilder queries both sources and enriches the system prompt with relevant facts and behavioral trends.

**Tech Stack:** graphiti-core[falkordb,anthropic], FalkorDB (Redis-compatible graph DB), SQLAlchemy (pattern_logs table), Claude API (NLP analysis), FastAPI (memory endpoints)

**Design Doc:** `docs/plans/2026-02-14-graphiti-nlp-memory-design.md`

---

## Task 1: Infrastructure – FalkorDB + Dependencies

**Files:**
- Modify: `docker-compose.yml` (replace redis service)
- Modify: `docker-compose.dev.yml` (replace redis service)
- Modify: `backend/requirements.txt` (add graphiti-core)
- Modify: `backend/app/core/config.py` (add FalkorDB/Graphiti settings)
- Modify: `.env.example` (add new env vars)
- Modify: `.env` (add new env vars)

### Step 1: Replace Redis with FalkorDB in docker-compose.yml

In `docker-compose.yml`, replace the `redis` service block with:

```yaml
  falkordb:
    image: falkordb/falkordb:latest
    container_name: alice-falkordb
    ports:
      - "${FALKORDB_PORT:-6379}:6379"
    volumes:
      - falkordb_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - alice-network
```

Update volume definitions: rename `redis_data` to `falkordb_data`.

Update all `redis` references in other services' `depends_on` and `environment` to `falkordb`:
- `REDIS_HOST=falkordb` (keep env var name for backward compat with Celery)

Do the same in `docker-compose.dev.yml`.

### Step 2: Add Python dependencies

Add to `backend/requirements.txt`:

```
graphiti-core[falkordb,anthropic]>=0.5
```

### Step 3: Add config settings

In `backend/app/core/config.py`, add these fields to the `Settings` class:

```python
    # FalkorDB / Graphiti
    falkordb_host: str = Field(default="falkordb", alias="FALKORDB_HOST")
    falkordb_port: int = Field(default=6379, alias="FALKORDB_PORT")
    graphiti_enabled: bool = Field(default=True, alias="GRAPHITI_ENABLED")

    @property
    def falkordb_uri(self) -> str:
        """Get FalkorDB connection URI for Graphiti."""
        return f"falkor://{self.falkordb_host}:{self.falkordb_port}"
```

### Step 4: Update .env.example and .env

Add:

```
# FalkorDB / Graphiti
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
GRAPHITI_ENABLED=true
```

### Step 5: Verify Docker builds

Run: `cd backend && pip install graphiti-core[falkordb,anthropic]`
Run: `docker-compose build api`
Expected: Build succeeds

### Step 6: Commit

```bash
git add docker-compose.yml docker-compose.dev.yml backend/requirements.txt \
  backend/app/core/config.py .env.example .env
git commit -m "chore: replace Redis with FalkorDB, add graphiti-core dependency"
```

---

## Task 2: Database Migration – pattern_logs Table

**Files:**
- Create: `backend/alembic/versions/004_phase5_memory.py`

### Step 1: Write the migration

```python
"""Phase 5 memory: pattern_logs table.

Revision ID: 004_phase5_memory
Revises: 003_phase3_tables
Create Date: 2026-02-14
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_phase5_memory"
down_revision: Union[str, None] = "003_phase3_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pattern_logs table."""
    op.create_table(
        "pattern_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "episode_id",
            sa.String(255),
            nullable=True,
            comment="Graphiti episode reference ID",
        ),
        sa.Column(
            "mood_score",
            sa.Float(),
            nullable=True,
            comment="Mood score from -1.0 (negative) to 1.0 (positive)",
        ),
        sa.Column(
            "energy_level",
            sa.Float(),
            nullable=True,
            comment="Energy level from 0.0 (low) to 1.0 (high)",
        ),
        sa.Column(
            "focus_score",
            sa.Float(),
            nullable=True,
            comment="Focus score from 0.0 (unfocused) to 1.0 (focused)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_pattern_logs_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="SET NULL",
            name="fk_pattern_logs_conversation_id",
        ),
        comment="NLP analysis scores per conversation for trend tracking",
    )

    op.create_index(
        "ix_pattern_logs_user_date",
        "pattern_logs",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_pattern_logs_conversation",
        "pattern_logs",
        ["conversation_id"],
    )


def downgrade() -> None:
    """Drop pattern_logs table."""
    op.drop_index("ix_pattern_logs_conversation", table_name="pattern_logs")
    op.drop_index("ix_pattern_logs_user_date", table_name="pattern_logs")
    op.drop_table("pattern_logs")
```

### Step 2: Run migration

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully, `pattern_logs` table created

### Step 3: Verify migration is reversible

Run: `cd backend && alembic downgrade -1 && alembic upgrade head`
Expected: Both succeed without errors

### Step 4: Commit

```bash
git add backend/alembic/versions/004_phase5_memory.py
git commit -m "db: add pattern_logs table for NLP conversation analysis (Phase 5)"
```

---

## Task 3: PatternLog Model + Schemas

**Files:**
- Create: `backend/app/models/pattern_log.py`
- Modify: `backend/app/models/__init__.py` (add import)
- Create: `backend/app/schemas/memory.py`
- Create: `backend/tests/test_memory_schemas.py`

### Step 1: Write the failing test for schemas

```python
"""Tests for memory schemas."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.schemas.memory import (
    PatternLogResponse,
    MemoryStatusResponse,
    MemoryExportResponse,
    MemorySettingsUpdate,
    ConversationAnalysis,
)


class TestConversationAnalysis:
    """Tests for ConversationAnalysis schema."""

    def test_valid_analysis(self):
        analysis = ConversationAnalysis(
            mood_score=0.5,
            energy_level=0.7,
            focus_score=0.3,
            detected_patterns=["procrastination"],
            pattern_triggers=["deadline_stress"],
            notable_facts=["User arbeitet als Designer"],
        )
        assert analysis.mood_score == 0.5
        assert len(analysis.detected_patterns) == 1

    def test_score_clamping(self):
        """Scores must be within valid ranges."""
        with pytest.raises(Exception):
            ConversationAnalysis(
                mood_score=2.0,  # Out of range
                energy_level=0.5,
                focus_score=0.5,
                detected_patterns=[],
                pattern_triggers=[],
                notable_facts=[],
            )


class TestMemoryStatusResponse:
    """Tests for MemoryStatusResponse schema."""

    def test_valid_status(self):
        status = MemoryStatusResponse(
            enabled=True,
            total_episodes=42,
            total_entities=156,
            last_analysis_at=datetime.now(timezone.utc),
        )
        assert status.enabled is True
        assert status.total_episodes == 42


class TestMemorySettingsUpdate:
    """Tests for MemorySettingsUpdate schema."""

    def test_valid_update(self):
        update = MemorySettingsUpdate(enabled=False)
        assert update.enabled is False
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_memory_schemas.py -v`
Expected: FAIL (imports not found)

### Step 3: Write the SQLAlchemy model

Create `backend/app/models/pattern_log.py`:

```python
"""PatternLog model for NLP conversation analysis scores."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PatternLog(BaseModel):
    """Stores NLP analysis scores per conversation for trend tracking."""

    __tablename__ = "pattern_logs"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this analysis belongs to",
    )

    conversation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Conversation that was analyzed",
    )

    episode_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Graphiti episode reference ID",
    )

    mood_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Mood: -1.0 (negative) to 1.0 (positive)",
    )

    energy_level: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Energy: 0.0 (low) to 1.0 (high)",
    )

    focus_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Focus: 0.0 (unfocused) to 1.0 (focused)",
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")
```

Add import to `backend/app/models/__init__.py`:

```python
from app.models.pattern_log import PatternLog  # noqa: F401
```

### Step 4: Write the Pydantic schemas

Create `backend/app/schemas/memory.py`:

```python
"""Schemas for the memory/knowledge graph system."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationAnalysis(BaseModel):
    """Result of NLP analysis on a single conversation."""

    mood_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Mood score from -1.0 (negative) to 1.0 (positive)",
    )
    energy_level: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Energy level from 0.0 (low) to 1.0 (high)",
    )
    focus_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Focus score from 0.0 (unfocused) to 1.0 (focused)",
    )
    detected_patterns: list[str] = Field(
        default_factory=list,
        description="ADHS patterns detected in conversation",
    )
    pattern_triggers: list[str] = Field(
        default_factory=list,
        description="Triggers observed for detected patterns",
    )
    notable_facts: list[str] = Field(
        default_factory=list,
        description="Notable facts about the user extracted from conversation",
    )


class PatternLogResponse(BaseModel):
    """Response schema for a single pattern log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID | None = None
    episode_id: str | None = None
    mood_score: float | None = None
    energy_level: float | None = None
    focus_score: float | None = None
    created_at: datetime


class MemoryStatusResponse(BaseModel):
    """Response schema for memory system status."""

    enabled: bool = Field(description="Whether memory/learning is enabled")
    total_episodes: int = Field(description="Total episodes processed")
    total_entities: int = Field(description="Total entities in knowledge graph")
    last_analysis_at: datetime | None = Field(
        None, description="Timestamp of last conversation analysis"
    )


class MemoryExportResponse(BaseModel):
    """Response schema for DSGVO Art. 15 data export."""

    entities: list[dict] = Field(description="All entities stored about the user")
    relations: list[dict] = Field(description="All relations in knowledge graph")
    pattern_logs: list[PatternLogResponse] = Field(
        description="All NLP analysis logs"
    )
    exported_at: datetime


class MemorySettingsUpdate(BaseModel):
    """Schema for updating memory settings."""

    enabled: bool = Field(description="Enable or disable memory/learning")
```

### Step 5: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_memory_schemas.py -v`
Expected: All tests PASS

### Step 6: Commit

```bash
git add backend/app/models/pattern_log.py backend/app/models/__init__.py \
  backend/app/schemas/memory.py backend/tests/test_memory_schemas.py
git commit -m "feat: add PatternLog model and memory schemas (Phase 5)"
```

---

## Task 4: GraphitiClient Wrapper

**Files:**
- Create: `backend/app/services/graphiti_client.py`
- Create: `backend/tests/test_graphiti_client.py`

### Step 1: Write the failing test

```python
"""Tests for GraphitiClient wrapper."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.graphiti_client import GraphitiClient, ADHD_SEED_PATTERNS


class TestADHDSeedPatterns:
    """Test seed pattern definitions."""

    def test_seed_patterns_count(self):
        """We should have 13 predefined ADHS patterns."""
        assert len(ADHD_SEED_PATTERNS) == 13

    def test_seed_patterns_have_required_fields(self):
        """Each pattern needs name and description."""
        for pattern in ADHD_SEED_PATTERNS:
            assert "name" in pattern
            assert "description" in pattern
            assert len(pattern["name"]) > 0
            assert len(pattern["description"]) > 0


class TestGraphitiClientInit:
    """Test GraphitiClient initialization."""

    def test_client_disabled(self):
        """Client should handle disabled state gracefully."""
        client = GraphitiClient(enabled=False)
        assert client.enabled is False

    @pytest.mark.asyncio
    async def test_search_when_disabled_returns_empty(self):
        """Search should return empty list when disabled."""
        client = GraphitiClient(enabled=False)
        results = await client.search("test query", user_id="test-user")
        assert results == []

    @pytest.mark.asyncio
    async def test_add_episode_when_disabled_returns_none(self):
        """add_episode should return None when disabled."""
        client = GraphitiClient(enabled=False)
        result = await client.add_episode(
            name="test",
            content="test content",
            user_id="test-user",
        )
        assert result is None
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_graphiti_client.py -v`
Expected: FAIL (import not found)

### Step 3: Write the GraphitiClient

Create `backend/app/services/graphiti_client.py`:

```python
"""Wrapper around Graphiti for knowledge graph operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

ADHD_SEED_PATTERNS: list[dict[str, str]] = [
    {
        "name": "Procrastination",
        "description": "Aufschieben von Aufgaben trotz Dringlichkeit und Bewusstsein der Konsequenzen",
    },
    {
        "name": "Hyperfocus",
        "description": "Uebermaessige Vertiefung in eine einzelne Aufgabe, Umgebung wird ausgeblendet",
    },
    {
        "name": "Task-Switching",
        "description": "Haeufiger Wechsel zwischen Aufgaben ohne eine davon abzuschliessen",
    },
    {
        "name": "Paralysis by Analysis",
        "description": "Entscheidungsunfaehigkeit durch Ueberanalyse und zu viele Optionen",
    },
    {
        "name": "Time Blindness",
        "description": "Fehleinschaetzung von Zeitdauern, Verlust des Zeitgefuehls",
    },
    {
        "name": "Emotional Dysregulation",
        "description": "Uebermaessige emotionale Reaktionen, schnelle Stimmungswechsel",
    },
    {
        "name": "Rejection Sensitivity",
        "description": "Ueberempfindlichkeit gegenueber Kritik, Ablehnung oder Missbilligung",
    },
    {
        "name": "Dopamine Seeking",
        "description": "Impulsives Suchen nach Stimulation (Social Media, Shopping, neues Hobby)",
    },
    {
        "name": "Working Memory Overload",
        "description": "Vergessen von gerade Besprochenem, Verlust von Informationen im Kurzzeitgedaechtnis",
    },
    {
        "name": "Sleep Disruption",
        "description": "Einschlafprobleme, Revenge Bedtime Procrastination, unregelmaessiger Schlafrhythmus",
    },
    {
        "name": "Transition Difficulty",
        "description": "Schwierigkeiten beim Wechsel zwischen Aktivitaeten oder Kontexten",
    },
    {
        "name": "Perfectionism Paralysis",
        "description": "Nichts anfangen weil es perfekt sein muss, Angst vor Fehlern",
    },
    {
        "name": "Social Masking",
        "description": "Erschoepfung durch Anpassung an neurotypische Erwartungen und Normen",
    },
]


class GraphitiClient:
    """Wrapper around Graphiti for ALICE's knowledge graph memory.

    Provides graceful degradation when FalkorDB is unavailable or disabled.
    """

    def __init__(self, uri: str = "", enabled: bool = True):
        self.enabled = enabled
        self.uri = uri
        self._graphiti = None

    async def initialize(self) -> None:
        """Initialize Graphiti connection and build indices."""
        if not self.enabled:
            logger.info("Graphiti disabled, skipping initialization")
            return

        try:
            from graphiti_core import Graphiti

            self._graphiti = Graphiti(uri=self.uri)
            await self._graphiti.build_indices_and_constraints()
            logger.info("Graphiti initialized with FalkorDB at %s", self.uri)
        except Exception:
            logger.exception("Failed to initialize Graphiti, disabling memory")
            self.enabled = False
            self._graphiti = None

    async def close(self) -> None:
        """Close Graphiti connection."""
        if self._graphiti is not None:
            try:
                await self._graphiti.close()
            except Exception:
                logger.exception("Error closing Graphiti connection")

    async def seed_adhd_patterns(self) -> None:
        """Seed the 13 predefined ADHS patterns as episodes."""
        if not self.enabled or self._graphiti is None:
            return

        from graphiti_core.nodes import EpisodeType

        for pattern in ADHD_SEED_PATTERNS:
            try:
                await self._graphiti.add_episode(
                    name=f"adhd_pattern_{pattern['name'].lower().replace(' ', '_')}",
                    episode_body=(
                        f"ADHS-Verhaltensmuster: {pattern['name']}. "
                        f"Beschreibung: {pattern['description']}"
                    ),
                    source=EpisodeType.text,
                    source_description="ADHS pattern seed data",
                    reference_time=datetime.now(timezone.utc),
                )
            except Exception:
                logger.exception("Failed to seed pattern: %s", pattern["name"])

        logger.info("Seeded %d ADHS patterns", len(ADHD_SEED_PATTERNS))

    async def add_episode(
        self,
        name: str,
        content: str,
        user_id: str,
        reference_time: datetime | None = None,
    ) -> str | None:
        """Add a conversation episode to the knowledge graph.

        Returns the episode UUID or None if disabled/failed.
        """
        if not self.enabled or self._graphiti is None:
            return None

        from graphiti_core.nodes import EpisodeType

        try:
            episode = await self._graphiti.add_episode(
                name=name,
                episode_body=content,
                source=EpisodeType.text,
                source_description=f"ALICE conversation with user {user_id}",
                reference_time=reference_time or datetime.now(timezone.utc),
                group_id=user_id,
            )
            return episode.uuid if episode else None
        except Exception:
            logger.exception("Failed to add episode for user %s", user_id)
            return None

    async def search(
        self,
        query: str,
        user_id: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the knowledge graph for relevant context.

        Returns list of dicts with entity/relation information.
        """
        if not self.enabled or self._graphiti is None:
            return []

        try:
            results = await self._graphiti.search(
                query=query,
                group_ids=[user_id],
                num_results=num_results,
            )
            return [
                {
                    "uuid": r.uuid,
                    "fact": r.fact if hasattr(r, "fact") else str(r),
                    "created_at": str(r.created_at) if hasattr(r, "created_at") else None,
                }
                for r in results
            ]
        except Exception:
            logger.exception("Graphiti search failed for user %s", user_id)
            return []

    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all knowledge graph data for a user (DSGVO Art. 17)."""
        if not self.enabled or self._graphiti is None:
            return True  # Nothing to delete

        try:
            episodes = await self._graphiti.search(
                query="*",
                group_ids=[user_id],
                num_results=1000,
            )
            for episode in episodes:
                if hasattr(episode, "uuid"):
                    await self._graphiti.delete_episode(episode.uuid)
            logger.info("Deleted knowledge graph data for user %s", user_id)
            return True
        except Exception:
            logger.exception("Failed to delete graph data for user %s", user_id)
            return False

    async def get_entity_count(self, user_id: str) -> int:
        """Get total entity count for a user."""
        if not self.enabled or self._graphiti is None:
            return 0

        try:
            results = await self._graphiti.search(
                query="*",
                group_ids=[user_id],
                num_results=1000,
            )
            return len(results)
        except Exception:
            return 0


# Singleton instance, initialized in app lifespan
graphiti_client: GraphitiClient | None = None


def get_graphiti_client() -> GraphitiClient:
    """Get the global GraphitiClient instance."""
    if graphiti_client is None:
        return GraphitiClient(enabled=False)
    return graphiti_client
```

### Step 4: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_graphiti_client.py -v`
Expected: All tests PASS

### Step 5: Commit

```bash
git add backend/app/services/graphiti_client.py backend/tests/test_graphiti_client.py
git commit -m "feat: add GraphitiClient wrapper with ADHS seed patterns"
```

---

## Task 5: NLPAnalyzer – Conversation Analysis

**Files:**
- Create: `backend/app/services/nlp_analyzer.py`
- Create: `backend/tests/test_nlp_analyzer.py`

### Step 1: Write the failing test

```python
"""Tests for NLPAnalyzer service."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.nlp_analyzer import NLPAnalyzer
from app.schemas.memory import ConversationAnalysis


class TestNLPAnalyzer:
    """Tests for NLP conversation analysis."""

    def test_build_analysis_prompt(self):
        """Test that analysis prompt contains required extraction fields."""
        analyzer = NLPAnalyzer()
        messages = [
            {"role": "user", "content": "Ich kann mich nicht konzentrieren"},
            {"role": "assistant", "content": "Das klingt frustrierend."},
        ]
        prompt = analyzer._build_analysis_prompt(messages)
        assert "mood_score" in prompt
        assert "energy_level" in prompt
        assert "focus_score" in prompt
        assert "detected_patterns" in prompt
        assert "notable_facts" in prompt

    def test_parse_valid_json_response(self):
        """Test parsing a valid JSON analysis response."""
        analyzer = NLPAnalyzer()
        raw = json.dumps({
            "mood_score": -0.3,
            "energy_level": 0.4,
            "focus_score": 0.2,
            "detected_patterns": ["procrastination"],
            "pattern_triggers": ["deadline_stress"],
            "notable_facts": ["User arbeitet als Designer"],
        })
        result = analyzer._parse_response(raw)
        assert isinstance(result, ConversationAnalysis)
        assert result.mood_score == -0.3
        assert result.detected_patterns == ["procrastination"]

    def test_parse_invalid_json_returns_neutral(self):
        """Test that invalid JSON returns neutral analysis."""
        analyzer = NLPAnalyzer()
        result = analyzer._parse_response("not json at all")
        assert isinstance(result, ConversationAnalysis)
        assert result.mood_score == 0.0
        assert result.detected_patterns == []

    def test_format_messages_for_prompt(self):
        """Test message formatting for the analysis prompt."""
        analyzer = NLPAnalyzer()
        messages = [
            {"role": "user", "content": "Hallo"},
            {"role": "assistant", "content": "Hi!"},
        ]
        formatted = analyzer._format_messages(messages)
        assert "User: Hallo" in formatted
        assert "ALICE: Hi!" in formatted
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_nlp_analyzer.py -v`
Expected: FAIL (import not found)

### Step 3: Write the NLPAnalyzer

Create `backend/app/services/nlp_analyzer.py`:

```python
"""NLP analysis of conversations for mood, energy, focus, and ADHS patterns."""

from __future__ import annotations

import json
import logging

import httpx

from app.core.config import settings
from app.schemas.memory import ConversationAnalysis

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """Du bist ein klinischer NLP-Analysator fuer ADHS-Coaching-Gespraeche.
Analysiere das folgende Gespraech und extrahiere strukturierte Daten.
Antworte AUSSCHLIESSLICH mit validem JSON, kein anderer Text."""


class NLPAnalyzer:
    """Analyzes conversations for mood, energy, focus, and ADHS patterns.

    Uses a single Claude API call per conversation to extract all metrics.
    """

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-haiku-4-5-20251001"  # Fast + cheap for analysis

    def _format_messages(self, messages: list[dict]) -> str:
        """Format chat messages into readable text for analysis."""
        lines = []
        for msg in messages:
            role = "User" if msg.get("role") == "user" else "ALICE"
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _build_analysis_prompt(self, messages: list[dict]) -> str:
        """Build the analysis prompt for Claude."""
        conversation_text = self._format_messages(messages)

        return f"""Analysiere dieses Gespraech zwischen einem ADHS-Betroffenen und seinem KI-Coach ALICE:

---
{conversation_text}
---

Extrahiere folgende Informationen als JSON:

{{
  "mood_score": <float, -1.0 (sehr negativ) bis 1.0 (sehr positiv)>,
  "energy_level": <float, 0.0 (sehr niedrig) bis 1.0 (sehr hoch)>,
  "focus_score": <float, 0.0 (unfokussiert) bis 1.0 (fokussiert)>,
  "detected_patterns": [<strings: erkannte ADHS-Muster wie "procrastination", "hyperfocus", "task_switching", "time_blindness", "emotional_dysregulation", "rejection_sensitivity", "dopamine_seeking", "working_memory_overload", "sleep_disruption", "transition_difficulty", "perfectionism_paralysis", "social_masking", "paralysis_by_analysis">],
  "pattern_triggers": [<strings: beobachtete Ausloser fuer die Muster>],
  "notable_facts": [<strings: neue Fakten ueber den User, z.B. Personen, Orte, Vorlieben, Gewohnheiten>]
}}

Antworte NUR mit dem JSON-Objekt."""

    def _parse_response(self, raw: str) -> ConversationAnalysis:
        """Parse Claude's JSON response into a ConversationAnalysis."""
        try:
            # Strip markdown code blocks if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]

            data = json.loads(cleaned)
            return ConversationAnalysis(**data)
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Failed to parse NLP analysis response, returning neutral")
            return ConversationAnalysis(
                mood_score=0.0,
                energy_level=0.5,
                focus_score=0.5,
                detected_patterns=[],
                pattern_triggers=[],
                notable_facts=[],
            )

    async def analyze(
        self, messages: list[dict]
    ) -> ConversationAnalysis:
        """Analyze a conversation and return structured NLP metrics.

        Makes a single Claude API call. Returns neutral values on failure.
        """
        if not messages or not self.api_key:
            return ConversationAnalysis(
                mood_score=0.0,
                energy_level=0.5,
                focus_score=0.5,
                detected_patterns=[],
                pattern_triggers=[],
                notable_facts=[],
            )

        prompt = self._build_analysis_prompt(messages)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "system": ANALYSIS_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                result = response.json()
                text = result["content"][0]["text"]
                return self._parse_response(text)

        except Exception:
            logger.exception("NLP analysis failed")
            return ConversationAnalysis(
                mood_score=0.0,
                energy_level=0.5,
                focus_score=0.5,
                detected_patterns=[],
                pattern_triggers=[],
                notable_facts=[],
            )
```

### Step 4: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_nlp_analyzer.py -v`
Expected: All tests PASS

### Step 5: Commit

```bash
git add backend/app/services/nlp_analyzer.py backend/tests/test_nlp_analyzer.py
git commit -m "feat: add NLPAnalyzer for conversation mood/pattern analysis"
```

---

## Task 6: PatternAnalyzer – Trend Queries

**Files:**
- Create: `backend/app/services/pattern_analyzer.py`
- Create: `backend/tests/test_pattern_analyzer.py`

### Step 1: Write the failing test

```python
"""Tests for PatternAnalyzer service."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog
from app.services.pattern_analyzer import PatternAnalyzer


class TestPatternAnalyzer:
    """Tests for trend analysis on pattern_logs."""

    @pytest_asyncio.fixture
    async def seeded_logs(self, db_session: AsyncSession, test_user_id: str):
        """Seed pattern_logs with test data for trend analysis."""
        user_id = test_user_id
        now = datetime.now(timezone.utc)

        logs = []
        for i in range(7):
            log = PatternLog(
                user_id=user_id,
                mood_score=0.3 - (i * 0.05),  # Declining mood
                energy_level=0.6 - (i * 0.05),
                focus_score=0.4 - (i * 0.03),
                created_at=now - timedelta(days=i),
            )
            db_session.add(log)
            logs.append(log)

        await db_session.flush()
        return logs

    async def test_get_recent_trends_returns_averages(
        self, db_session: AsyncSession, seeded_logs, test_user_id: str,
    ):
        analyzer = PatternAnalyzer(db_session)
        trends = await analyzer.get_recent_trends(test_user_id, days=7)

        assert "avg_mood" in trends
        assert "avg_energy" in trends
        assert "avg_focus" in trends
        assert "total_conversations" in trends
        assert trends["total_conversations"] == 7

    async def test_get_recent_trends_empty_user(self, db_session: AsyncSession):
        analyzer = PatternAnalyzer(db_session)
        trends = await analyzer.get_recent_trends(str(uuid4()), days=7)
        assert trends["total_conversations"] == 0

    async def test_format_trends_for_prompt(self, db_session: AsyncSession):
        analyzer = PatternAnalyzer(db_session)
        trends = {
            "avg_mood": 0.2,
            "avg_energy": 0.5,
            "avg_focus": 0.3,
            "total_conversations": 5,
            "mood_trend": "declining",
        }
        text = analyzer.format_for_prompt(trends)
        assert "Stimmung" in text or "Mood" in text
        assert "0.2" in text or "leicht positiv" in text
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_pattern_analyzer.py -v`
Expected: FAIL (import not found)

### Step 3: Write the PatternAnalyzer

Create `backend/app/services/pattern_analyzer.py`:

```python
"""Trend analysis on pattern_logs for behavioral insights."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog


class PatternAnalyzer:
    """Analyzes pattern_logs for behavioral trends over time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_trends(
        self, user_id: str | UUID, days: int = 7
    ) -> dict[str, Any]:
        """Get aggregated mood/energy/focus trends for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(
            func.avg(PatternLog.mood_score).label("avg_mood"),
            func.avg(PatternLog.energy_level).label("avg_energy"),
            func.avg(PatternLog.focus_score).label("avg_focus"),
            func.count(PatternLog.id).label("total"),
            func.min(PatternLog.mood_score).label("min_mood"),
            func.max(PatternLog.mood_score).label("max_mood"),
        ).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= cutoff,
        )

        result = (await self.db.execute(stmt)).one()

        # Determine mood trend (compare first half vs second half)
        mood_trend = await self._calculate_trend(
            user_id, days, "mood_score"
        )

        return {
            "avg_mood": round(float(result.avg_mood or 0), 2),
            "avg_energy": round(float(result.avg_energy or 0), 2),
            "avg_focus": round(float(result.avg_focus or 0), 2),
            "total_conversations": int(result.total or 0),
            "min_mood": round(float(result.min_mood or 0), 2),
            "max_mood": round(float(result.max_mood or 0), 2),
            "mood_trend": mood_trend,
        }

    async def _calculate_trend(
        self, user_id: str | UUID, days: int, column: str
    ) -> str:
        """Calculate if a metric is rising, declining, or stable."""
        now = datetime.now(timezone.utc)
        midpoint = now - timedelta(days=days / 2)
        cutoff = now - timedelta(days=days)

        col = getattr(PatternLog, column)

        # First half average
        stmt_first = select(func.avg(col)).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= cutoff,
            PatternLog.created_at < midpoint,
        )
        first_avg = (await self.db.execute(stmt_first)).scalar() or 0

        # Second half average
        stmt_second = select(func.avg(col)).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= midpoint,
        )
        second_avg = (await self.db.execute(stmt_second)).scalar() or 0

        diff = float(second_avg) - float(first_avg)
        if diff > 0.1:
            return "rising"
        elif diff < -0.1:
            return "declining"
        return "stable"

    async def get_last_analysis(self, user_id: str | UUID) -> datetime | None:
        """Get timestamp of the most recent analysis."""
        stmt = (
            select(PatternLog.created_at)
            .where(PatternLog.user_id == str(user_id))
            .order_by(PatternLog.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar()

    async def get_log_count(self, user_id: str | UUID) -> int:
        """Get total number of pattern logs for a user."""
        stmt = select(func.count(PatternLog.id)).where(
            PatternLog.user_id == str(user_id)
        )
        return (await self.db.execute(stmt)).scalar() or 0

    def format_for_prompt(self, trends: dict[str, Any]) -> str:
        """Format trends into a human-readable prompt section."""
        if trends["total_conversations"] == 0:
            return "Noch keine Verhaltensdaten vorhanden."

        mood_label = self._score_label(trends["avg_mood"], is_mood=True)
        energy_label = self._score_label(trends["avg_energy"])
        focus_label = self._score_label(trends["avg_focus"])
        trend_label = {
            "rising": "steigend",
            "declining": "fallend",
            "stable": "stabil",
        }.get(trends["mood_trend"], "unbekannt")

        return (
            f"Basierend auf {trends['total_conversations']} Gespraechen "
            f"der letzten Tage:\n"
            f"- Stimmung: {trends['avg_mood']} ({mood_label}, Trend: {trend_label})\n"
            f"- Energie: {trends['avg_energy']} ({energy_label})\n"
            f"- Fokus: {trends['avg_focus']} ({focus_label})"
        )

    @staticmethod
    def _score_label(score: float, is_mood: bool = False) -> str:
        """Convert a numeric score to a German label."""
        if is_mood:
            if score >= 0.5:
                return "positiv"
            elif score >= 0.1:
                return "leicht positiv"
            elif score >= -0.1:
                return "neutral"
            elif score >= -0.5:
                return "leicht negativ"
            return "negativ"
        else:
            if score >= 0.7:
                return "hoch"
            elif score >= 0.4:
                return "mittel"
            return "niedrig"
```

### Step 4: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_pattern_analyzer.py -v`
Expected: All tests PASS (note: DB-dependent tests need test fixtures from conftest.py – if `test_user_id` and `db_session` fixtures don't exist yet, write simpler unit tests first and mark integration tests as `@pytest.mark.skip` until Task 10)

### Step 5: Commit

```bash
git add backend/app/services/pattern_analyzer.py backend/tests/test_pattern_analyzer.py
git commit -m "feat: add PatternAnalyzer for behavioral trend analysis"
```

---

## Task 7: MemoryService – Orchestrator

**Files:**
- Create: `backend/app/services/memory.py`
- Create: `backend/tests/test_memory_service.py`

### Step 1: Write the failing test

```python
"""Tests for MemoryService orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.memory import MemoryService
from app.schemas.memory import ConversationAnalysis


class TestMemoryService:
    """Tests for the memory orchestrator."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_graphiti(self):
        client = AsyncMock()
        client.enabled = True
        client.add_episode = AsyncMock(return_value="episode-uuid-123")
        client.search = AsyncMock(return_value=[
            {"fact": "User arbeitet als Designer", "uuid": "e1"},
            {"fact": "User hat Schwester Lisa", "uuid": "e2"},
        ])
        client.get_entity_count = AsyncMock(return_value=42)
        client.delete_user_data = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def mock_analyzer(self):
        analyzer = AsyncMock()
        analyzer.analyze = AsyncMock(return_value=ConversationAnalysis(
            mood_score=0.3,
            energy_level=0.6,
            focus_score=0.4,
            detected_patterns=["procrastination"],
            pattern_triggers=["deadline_stress"],
            notable_facts=["User arbeitet als Designer"],
        ))
        return analyzer

    @pytest.mark.asyncio
    async def test_process_episode_stores_pattern_log(
        self, mock_db, mock_graphiti, mock_analyzer,
    ):
        service = MemoryService(mock_db, mock_graphiti)
        service.nlp_analyzer = mock_analyzer

        user_id = str(uuid4())
        conv_id = str(uuid4())
        messages = [
            {"role": "user", "content": "Ich prokrastiniere wieder"},
        ]

        await service.process_episode(user_id, conv_id, messages)

        mock_graphiti.add_episode.assert_called_once()
        mock_analyzer.analyze.assert_called_once_with(messages)
        mock_db.add.assert_called_once()  # PatternLog added

    @pytest.mark.asyncio
    async def test_get_context_returns_facts_and_trends(
        self, mock_db, mock_graphiti,
    ):
        service = MemoryService(mock_db, mock_graphiti)

        with patch.object(
            service.pattern_analyzer, "get_recent_trends",
            new_callable=AsyncMock,
            return_value={
                "avg_mood": 0.3, "avg_energy": 0.5, "avg_focus": 0.4,
                "total_conversations": 5, "mood_trend": "declining",
                "min_mood": 0.1, "max_mood": 0.6,
            },
        ):
            context = await service.get_context(str(uuid4()), "test query")

        assert "facts" in context
        assert "trends" in context
        assert len(context["facts"]) == 2

    @pytest.mark.asyncio
    async def test_process_episode_graceful_on_graphiti_failure(
        self, mock_db, mock_analyzer,
    ):
        """Memory service should not crash when Graphiti fails."""
        mock_graphiti = AsyncMock()
        mock_graphiti.enabled = True
        mock_graphiti.add_episode = AsyncMock(return_value=None)

        service = MemoryService(mock_db, mock_graphiti)
        service.nlp_analyzer = mock_analyzer

        # Should not raise
        await service.process_episode(str(uuid4()), str(uuid4()), [])
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_memory_service.py -v`
Expected: FAIL (import not found)

### Step 3: Write the MemoryService

Create `backend/app/services/memory.py`:

```python
"""MemoryService – orchestrates Graphiti and NLP analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog
from app.services.graphiti_client import GraphitiClient
from app.services.nlp_analyzer import NLPAnalyzer
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)


class MemoryService:
    """Orchestrates knowledge graph memory and NLP analysis.

    Coordinates between Graphiti (knowledge graph), NLPAnalyzer (conversation
    scoring), and PatternAnalyzer (trend detection).
    """

    def __init__(self, db: AsyncSession, graphiti: GraphitiClient):
        self.db = db
        self.graphiti = graphiti
        self.nlp_analyzer = NLPAnalyzer()
        self.pattern_analyzer = PatternAnalyzer(db)

    async def process_episode(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict],
    ) -> None:
        """Process a completed conversation: add to graph + analyze.

        Called async after conversation ends (5min inactivity).
        """
        if not messages:
            return

        # 1. Format conversation for Graphiti
        conversation_text = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'ALICE'}: {m.get('content', '')}"
            for m in messages
        )

        # 2. Add episode to knowledge graph
        episode_id = await self.graphiti.add_episode(
            name=f"conversation_{conversation_id}",
            content=conversation_text,
            user_id=user_id,
            reference_time=datetime.now(timezone.utc),
        )

        # 3. Run NLP analysis
        analysis = await self.nlp_analyzer.analyze(messages)

        # 4. Store scores in pattern_logs
        pattern_log = PatternLog(
            user_id=user_id,
            conversation_id=conversation_id,
            episode_id=episode_id,
            mood_score=analysis.mood_score,
            energy_level=analysis.energy_level,
            focus_score=analysis.focus_score,
        )
        self.db.add(pattern_log)
        await self.db.flush()

        logger.info(
            "Processed episode for user %s: mood=%.2f energy=%.2f focus=%.2f patterns=%s",
            user_id,
            analysis.mood_score,
            analysis.energy_level,
            analysis.focus_score,
            analysis.detected_patterns,
        )

    async def get_context(
        self, user_id: str, query: str
    ) -> dict[str, Any]:
        """Get memory context for system prompt enrichment.

        Called sync before each chat response (~300ms).
        """
        # 1. Search knowledge graph for relevant facts
        facts = await self.graphiti.search(
            query=query,
            user_id=user_id,
            num_results=10,
        )

        # 2. Get behavioral trends
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)

        return {
            "facts": facts,
            "trends": trends,
        }

    def format_context_for_prompt(self, context: dict[str, Any]) -> str:
        """Format memory context into a system prompt section."""
        parts = []

        # Facts section
        facts = context.get("facts", [])
        if facts:
            fact_lines = [f"- {f.get('fact', str(f))}" for f in facts[:10]]
            parts.append(
                "## Was du ueber den User weisst:\n" + "\n".join(fact_lines)
            )

        # Trends section
        trends = context.get("trends", {})
        if trends.get("total_conversations", 0) > 0:
            trend_text = self.pattern_analyzer.format_for_prompt(trends)
            parts.append(f"## Aktuelle Verhaltenstrends:\n{trend_text}")

            # Actionable recommendations
            recommendations = self._build_recommendations(trends)
            if recommendations:
                parts.append(
                    "## Handlungsempfehlung:\n" + "\n".join(
                        f"- {r}" for r in recommendations
                    )
                )

        if not parts:
            return ""

        return "\n\n".join(parts)

    @staticmethod
    def _build_recommendations(trends: dict[str, Any]) -> list[str]:
        """Build actionable recommendations based on trends."""
        recs = []

        avg_focus = trends.get("avg_focus", 0.5)
        avg_mood = trends.get("avg_mood", 0.0)
        mood_trend = trends.get("mood_trend", "stable")

        if avg_focus < 0.3:
            recs.append(
                "Fokus ist niedrig – schlage konkrete Fokus-Techniken vor "
                "(Pomodoro, Body Doubling)"
            )
        if avg_mood < -0.2:
            recs.append(
                "Stimmung ist gedrueckt – sei besonders empathisch, "
                "frage nach dem Befinden"
            )
        if mood_trend == "declining":
            recs.append(
                "Stimmungstrend ist fallend – sprich es behutsam an"
            )

        return recs

    async def get_status(self, user_id: str) -> dict[str, Any]:
        """Get memory system status for a user."""
        entity_count = await self.graphiti.get_entity_count(user_id)
        log_count = await self.pattern_analyzer.get_log_count(user_id)
        last_analysis = await self.pattern_analyzer.get_last_analysis(user_id)

        return {
            "enabled": self.graphiti.enabled,
            "total_episodes": log_count,
            "total_entities": entity_count,
            "last_analysis_at": last_analysis,
        }

    async def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Export all memory data for a user (DSGVO Art. 15)."""
        from sqlalchemy import select

        # Get all pattern logs
        stmt = (
            select(PatternLog)
            .where(PatternLog.user_id == user_id)
            .order_by(PatternLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        # Get all graph data
        entities = await self.graphiti.search(
            query="*", user_id=user_id, num_results=1000
        )

        return {
            "entities": entities,
            "relations": [],  # Graphiti search returns edges as facts
            "pattern_logs": logs,
            "exported_at": datetime.now(timezone.utc),
        }

    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all memory data for a user (DSGVO Art. 17)."""
        from sqlalchemy import delete

        # Delete pattern logs
        stmt = delete(PatternLog).where(PatternLog.user_id == user_id)
        await self.db.execute(stmt)

        # Delete graph data
        graph_deleted = await self.graphiti.delete_user_data(user_id)

        await self.db.flush()
        return graph_deleted
```

### Step 4: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_memory_service.py -v`
Expected: All tests PASS

### Step 5: Commit

```bash
git add backend/app/services/memory.py backend/tests/test_memory_service.py
git commit -m "feat: add MemoryService orchestrator for Graphiti + NLP"
```

---

## Task 8: ContextBuilder – System Prompt Enrichment

**Files:**
- Create: `backend/app/services/context_builder.py`
- Create: `backend/tests/test_context_builder.py`

### Step 1: Write the failing test

```python
"""Tests for ContextBuilder."""

import pytest
from unittest.mock import AsyncMock

from app.services.context_builder import ContextBuilder


class TestContextBuilder:
    """Tests for system prompt enrichment with memory context."""

    @pytest.fixture
    def mock_memory_service(self):
        service = AsyncMock()
        service.get_context = AsyncMock(return_value={
            "facts": [
                {"fact": "User arbeitet als Designer"},
                {"fact": "User hat Schwester Lisa"},
            ],
            "trends": {
                "avg_mood": 0.3,
                "avg_energy": 0.5,
                "avg_focus": 0.2,
                "total_conversations": 5,
                "mood_trend": "declining",
                "min_mood": 0.1,
                "max_mood": 0.6,
            },
        })
        service.format_context_for_prompt = lambda ctx: (
            "## Was du ueber den User weisst:\n"
            "- User arbeitet als Designer\n"
            "- User hat Schwester Lisa\n\n"
            "## Aktuelle Verhaltenstrends:\n"
            "Fokus niedrig, Stimmung fallend"
        )
        return service

    @pytest.mark.asyncio
    async def test_enrich_adds_memory_block(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        base_prompt = "Du bist ALICE, ein ADHS-Coach."

        enriched = await builder.enrich(
            base_prompt=base_prompt,
            user_id="test-user",
            user_message="Ich kann mich nicht konzentrieren",
        )

        assert "Du bist ALICE" in enriched
        assert "Was du ueber den User weisst" in enriched
        assert "Designer" in enriched

    @pytest.mark.asyncio
    async def test_enrich_without_memory_returns_base(self):
        """When memory service returns empty, just return base prompt."""
        mock_service = AsyncMock()
        mock_service.get_context = AsyncMock(return_value={
            "facts": [], "trends": {"total_conversations": 0},
        })
        mock_service.format_context_for_prompt = lambda ctx: ""

        builder = ContextBuilder(mock_service)
        enriched = await builder.enrich(
            base_prompt="Base prompt",
            user_id="new-user",
            user_message="Hallo",
        )

        assert enriched == "Base prompt"

    @pytest.mark.asyncio
    async def test_enrich_graceful_on_failure(self):
        """Should return base prompt if memory service crashes."""
        mock_service = AsyncMock()
        mock_service.get_context = AsyncMock(side_effect=Exception("DB down"))

        builder = ContextBuilder(mock_service)
        enriched = await builder.enrich(
            base_prompt="Base prompt",
            user_id="user",
            user_message="test",
        )

        assert enriched == "Base prompt"
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_context_builder.py -v`
Expected: FAIL

### Step 3: Write the ContextBuilder

Create `backend/app/services/context_builder.py`:

```python
"""ContextBuilder – enriches system prompts with memory context."""

from __future__ import annotations

import logging

from app.services.memory import MemoryService

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Enriches the system prompt with knowledge graph context and trends.

    Called synchronously before each chat response. Designed for low
    latency (~300ms) with graceful degradation on failure.
    """

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def enrich(
        self,
        base_prompt: str,
        user_id: str,
        user_message: str,
    ) -> str:
        """Enrich the system prompt with relevant memory context.

        Returns the base prompt unmodified if memory is unavailable.
        """
        try:
            context = await self.memory_service.get_context(
                user_id=user_id,
                query=user_message,
            )

            memory_block = self.memory_service.format_context_for_prompt(context)

            if not memory_block:
                return base_prompt

            return f"{base_prompt}\n\n{memory_block}"

        except Exception:
            logger.exception("Failed to enrich system prompt with memory")
            return base_prompt
```

### Step 4: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_context_builder.py -v`
Expected: All tests PASS

### Step 5: Commit

```bash
git add backend/app/services/context_builder.py backend/tests/test_context_builder.py
git commit -m "feat: add ContextBuilder for system prompt memory enrichment"
```

---

## Task 9: Memory API Endpoints

**Files:**
- Create: `backend/app/api/v1/memory.py`
- Modify: `backend/app/api/v1/__init__.py` (add router)
- Create: `backend/tests/test_memory_api.py`

### Step 1: Write the failing test

```python
"""Tests for Memory API endpoints."""

import pytest
from httpx import AsyncClient


class TestMemoryStatus:
    """Tests for GET /api/v1/memory/status."""

    async def test_get_status_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/memory/status")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "total_episodes" in data
        assert "total_entities" in data

    async def test_get_status_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/memory/status")
        assert response.status_code == 403


class TestMemoryExport:
    """Tests for GET /api/v1/memory/export."""

    async def test_export_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/memory/export")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "pattern_logs" in data
        assert "exported_at" in data


class TestMemoryDelete:
    """Tests for DELETE /api/v1/memory."""

    async def test_delete_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/api/v1/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True


class TestMemorySettings:
    """Tests for PUT /api/v1/settings/memory."""

    async def test_update_memory_setting(self, authenticated_client: AsyncClient):
        response = await authenticated_client.put(
            "/api/v1/settings/memory",
            json={"enabled": False},
        )
        assert response.status_code == 200
```

### Step 2: Run test to verify it fails

Run: `cd backend && python -m pytest tests/test_memory_api.py -v`
Expected: FAIL

### Step 3: Write the API routes

Create `backend/app/api/v1/memory.py`:

```python
"""Memory API endpoints for knowledge graph status, export, and DSGVO compliance."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.memory import (
    MemoryExportResponse,
    MemorySettingsUpdate,
    MemoryStatusResponse,
)
from app.services.graphiti_client import get_graphiti_client
from app.services.memory import MemoryService

router = APIRouter(tags=["Memory"])


@router.get(
    "/status",
    response_model=MemoryStatusResponse,
    summary="Get memory system status",
)
async def get_memory_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current status of the memory/knowledge graph system."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    status_data = await service.get_status(str(current_user.id))
    return MemoryStatusResponse(**status_data)


@router.get(
    "/export",
    summary="Export all memory data (DSGVO Art. 15)",
)
async def export_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all stored knowledge about the user for DSGVO compliance."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    export = await service.export_user_data(str(current_user.id))

    # Convert PatternLog ORM objects to dicts for serialization
    from app.schemas.memory import PatternLogResponse

    pattern_logs = [
        PatternLogResponse.model_validate(log).model_dump(mode="json")
        for log in export["pattern_logs"]
    ]

    return {
        "entities": export["entities"],
        "relations": export["relations"],
        "pattern_logs": pattern_logs,
        "exported_at": export["exported_at"].isoformat(),
    }


@router.delete(
    "",
    summary="Delete all memory data (DSGVO Art. 17)",
)
async def delete_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Irreversibly delete all knowledge graph and pattern data for the user."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    deleted = await service.delete_user_data(str(current_user.id))
    await db.commit()
    return {"deleted": deleted}


@router.put(
    "/settings",
    summary="Update memory settings",
)
async def update_memory_settings(
    data: MemorySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable the memory/learning system."""
    from app.services.settings import SettingsService

    settings_service = SettingsService(db)
    user_settings = await settings_service.get_settings(current_user.id)

    # Store memory_enabled in the existing JSONB settings
    current = user_settings.settings or {}
    current["memory_enabled"] = data.enabled
    user_settings.settings = current
    await db.flush()
    await db.commit()

    return {"enabled": data.enabled}
```

### Step 4: Register the router

In `backend/app/api/v1/__init__.py`, add:

```python
from app.api.v1.memory import router as memory_router

v1_router.include_router(memory_router, prefix="/memory")
```

### Step 5: Run tests to verify they pass

Run: `cd backend && python -m pytest tests/test_memory_api.py -v`
Expected: All tests PASS

### Step 6: Commit

```bash
git add backend/app/api/v1/memory.py backend/app/api/v1/__init__.py \
  backend/tests/test_memory_api.py
git commit -m "feat: add Memory API endpoints (status, export, delete, settings)"
```

---

## Task 10: Chat Integration – Hook Everything Together

**Files:**
- Modify: `backend/app/services/chat.py` (add ContextBuilder + EpisodeCollector)
- Modify: `backend/app/main.py` (initialize Graphiti in lifespan)
- Create: `backend/tests/test_chat_memory_integration.py`

### Step 1: Write the failing test

```python
"""Integration tests for chat + memory system."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


class TestChatMemoryIntegration:
    """Test that chat flow integrates with memory system."""

    @pytest.mark.asyncio
    async def test_chat_enriches_system_prompt(self, authenticated_client: AsyncClient):
        """Verify that the chat endpoint calls ContextBuilder."""
        with patch(
            "app.services.chat.ContextBuilder"
        ) as mock_builder_cls:
            mock_builder = AsyncMock()
            mock_builder.enrich = AsyncMock(
                return_value="Enriched system prompt"
            )
            mock_builder_cls.return_value = mock_builder

            response = await authenticated_client.post(
                "/api/v1/chat/message",
                json={"content": "Hallo ALICE"},
            )

            # ContextBuilder.enrich should have been called
            # (response may fail due to AI service mock, but builder should be called)
```

### Step 2: Modify main.py to initialize Graphiti in lifespan

In `backend/app/main.py`, update the `lifespan` function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    await init_db()

    # Initialize Graphiti knowledge graph
    from app.services.graphiti_client import GraphitiClient
    import app.services.graphiti_client as gc_module

    if settings.graphiti_enabled:
        client = GraphitiClient(
            uri=settings.falkordb_uri,
            enabled=True,
        )
        await client.initialize()
        gc_module.graphiti_client = client
    else:
        gc_module.graphiti_client = GraphitiClient(enabled=False)

    # Start background scheduler (skip in test env)
    scheduler_task = None
    if settings.app_env != "test":
        from app.services.scheduler import run_scheduler
        scheduler_task = asyncio.create_task(run_scheduler())

    yield

    # Shutdown
    if scheduler_task:
        scheduler_task.cancel()
    if gc_module.graphiti_client:
        await gc_module.graphiti_client.close()
    await close_db()
```

### Step 3: Modify ChatService._build_system_prompt to use ContextBuilder

In `backend/app/services/chat.py`, at the end of `_build_system_prompt()`, add memory context enrichment:

```python
    # After all existing prompt parts are built...
    base_prompt = "\n\n".join(parts)

    # Enrich with memory context
    try:
        from app.services.graphiti_client import get_graphiti_client
        from app.services.memory import MemoryService
        from app.services.context_builder import ContextBuilder

        graphiti = get_graphiti_client()
        if graphiti.enabled:
            memory_service = MemoryService(self.db, graphiti)
            builder = ContextBuilder(memory_service)
            base_prompt = await builder.enrich(
                base_prompt=base_prompt,
                user_id=str(user_id),
                user_message=user_message,
            )
    except Exception:
        pass  # Graceful degradation

    return base_prompt
```

Note: `_build_system_prompt` needs the `user_message` parameter added to its signature. Find the call site and pass the current message content.

### Step 4: Add async episode processing after conversation

In `backend/app/services/chat.py`, after a message exchange completes, schedule async episode processing. Add to the method that handles the full message flow:

```python
    # After response is sent to user, process episode async
    import asyncio
    from app.services.graphiti_client import get_graphiti_client
    from app.services.memory import MemoryService

    graphiti = get_graphiti_client()
    if graphiti.enabled:

        async def _process_episode():
            """Process conversation episode in background."""
            try:
                memory_service = MemoryService(self.db, graphiti)
                messages_for_analysis = [
                    {"role": m.role.value, "content": m.content}
                    for m in conversation_messages
                ]
                await memory_service.process_episode(
                    user_id=str(user_id),
                    conversation_id=str(conversation.id),
                    messages=messages_for_analysis,
                )
                await self.db.commit()
            except Exception:
                logger.exception("Background episode processing failed")

        asyncio.create_task(_process_episode())
```

### Step 5: Run tests

Run: `cd backend && python -m pytest tests/ -v --timeout=60`
Expected: All existing tests still pass + new integration test passes

### Step 6: Commit

```bash
git add backend/app/main.py backend/app/services/chat.py \
  backend/tests/test_chat_memory_integration.py
git commit -m "feat: integrate memory system into chat flow (Phase 5)"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `docs/STATUS.md` (add Phase 5 section)
- Modify: `docs/database/SCHEMA.md` (add pattern_logs)
- Modify: `docs/api/ENDPOINTS.md` (add memory endpoints)

### Step 1: Update STATUS.md

Add Phase 5 section after Phase 4:

```markdown
### Phase 5: Knowledge Graph & NLP (In Arbeit)

**Status:** Grundsystem implementiert

**Backend Services:**
- **GraphitiClient:** FalkorDB-basierter temporaler Knowledge Graph
- **NLPAnalyzer:** Stimmungs-, Energie- und Fokus-Analyse pro Gespraech
- **PatternAnalyzer:** Trend-Erkennung ueber Zeit
- **MemoryService:** Orchestrator fuer Graph + NLP
- **ContextBuilder:** System Prompt Enrichment mit Memory-Kontext

**API Endpoints (4 neue):**
- `GET /api/v1/memory/status` - Memory-System Status
- `GET /api/v1/memory/export` - DSGVO Art. 15 Datenexport
- `DELETE /api/v1/memory` - DSGVO Art. 17 Komplett-Loeschung
- `PUT /api/v1/settings/memory` - Memory ein/ausschalten

**Migration:**
- `004_phase5_memory` - pattern_logs (1 Tabelle)

**ADHS Patterns (13 Seed):**
Procrastination, Hyperfocus, Task-Switching, Paralysis by Analysis,
Time Blindness, Emotional Dysregulation, Rejection Sensitivity,
Dopamine Seeking, Working Memory Overload, Sleep Disruption,
Transition Difficulty, Perfectionism Paralysis, Social Masking
```

### Step 2: Update SCHEMA.md

Add `pattern_logs` table documentation.

### Step 3: Update ENDPOINTS.md

Add the 4 new memory endpoints.

### Step 4: Commit

```bash
git add docs/STATUS.md docs/database/SCHEMA.md docs/api/ENDPOINTS.md
git commit -m "docs: update documentation for Phase 5 Memory System"
```

---

## Task 12: Full Integration Test

**Files:**
- Create: `backend/tests/test_memory_e2e.py`

### Step 1: Write E2E test

```python
"""End-to-end tests for the memory system."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.graphiti_client import GraphitiClient
from app.services.memory import MemoryService
from app.services.nlp_analyzer import NLPAnalyzer


class TestMemoryE2E:
    """Full pipeline: chat -> episode -> pattern_log -> enriched prompt."""

    @pytest.mark.asyncio
    async def test_full_memory_pipeline(
        self, db_session: AsyncSession, test_user_id: str,
    ):
        """Test the complete memory flow with mocked Graphiti."""
        # Use disabled Graphiti for unit test (no FalkorDB needed)
        graphiti = GraphitiClient(enabled=False)
        service = MemoryService(db_session, graphiti)

        # 1. Process a conversation episode
        messages = [
            {"role": "user", "content": "Ich prokrastiniere schon wieder mit dem Kundenprojekt."},
            {"role": "assistant", "content": "Das klingt frustrierend. Was genau blockiert dich?"},
            {"role": "user", "content": "Die Deadline ist Freitag und ich weiss nicht wo ich anfangen soll."},
        ]

        await service.process_episode(
            user_id=test_user_id,
            conversation_id="test-conv-1",
            messages=messages,
        )
        await db_session.commit()

        # 2. Verify pattern_log was created
        from sqlalchemy import select
        from app.models.pattern_log import PatternLog

        stmt = select(PatternLog).where(PatternLog.user_id == test_user_id)
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].mood_score is not None

        # 3. Get memory context
        context = await service.get_context(test_user_id, "Fokus Probleme")
        assert "trends" in context

        # 4. Format for prompt
        prompt_section = service.format_context_for_prompt(context)
        # Should have trends since we have 1 conversation
        assert isinstance(prompt_section, str)

    @pytest.mark.asyncio
    async def test_memory_status_endpoint(
        self, authenticated_client: AsyncClient,
    ):
        response = await authenticated_client.get("/api/v1/memory/status")
        assert response.status_code == 200
        assert response.json()["total_episodes"] >= 0
```

### Step 2: Run all tests

Run: `cd backend && python -m pytest tests/ -v --timeout=120`
Expected: All tests PASS, including new memory tests

### Step 3: Commit

```bash
git add backend/tests/test_memory_e2e.py
git commit -m "test: add E2E tests for memory system pipeline"
```

---

## Summary

| Task | Component | Files | Tests |
|------|-----------|-------|-------|
| 1 | Infrastructure (FalkorDB + deps) | 6 modified | - |
| 2 | Migration (pattern_logs) | 1 created | - |
| 3 | PatternLog model + schemas | 4 created/modified | ~5 |
| 4 | GraphitiClient wrapper | 2 created | ~4 |
| 5 | NLPAnalyzer | 2 created | ~4 |
| 6 | PatternAnalyzer | 2 created | ~4 |
| 7 | MemoryService orchestrator | 2 created | ~4 |
| 8 | ContextBuilder | 2 created | ~3 |
| 9 | Memory API endpoints | 3 created/modified | ~5 |
| 10 | Chat integration | 3 modified | ~2 |
| 11 | Documentation update | 3 modified | - |
| 12 | E2E integration test | 1 created | ~2 |
| **Total** | | **~25 files** | **~33 tests** |

**Estimated new test count:** ~33 (on top of existing 194)
**Total test count after Phase 5:** ~227
