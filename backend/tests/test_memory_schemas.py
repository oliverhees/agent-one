"""Tests for memory schemas (pure Pydantic, no database required)."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.memory import (
    ConversationAnalysis,
    MemoryExportResponse,
    MemorySettingsUpdate,
    MemoryStatusResponse,
    PatternLogResponse,
)


# ---------------------------------------------------------------------------
# Override DB fixtures from conftest.py — these tests are pure Pydantic
# and do not need a database connection.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_tables():
    """No-op override: schema tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: schema tests don't need database setup."""
    yield


# ===========================================================================
# ConversationAnalysis
# ===========================================================================

class TestConversationAnalysis:
    """Tests for ConversationAnalysis schema."""

    def test_valid_analysis(self):
        """Valid analysis with all fields should work."""
        analysis = ConversationAnalysis(
            mood_score=0.5,
            energy_level=0.7,
            focus_score=0.3,
            detected_patterns=["procrastination"],
            pattern_triggers=["deadline_stress"],
            notable_facts=["User arbeitet als Designer"],
        )
        assert analysis.mood_score == 0.5
        assert analysis.energy_level == 0.7
        assert analysis.focus_score == 0.3
        assert len(analysis.detected_patterns) == 1
        assert analysis.detected_patterns[0] == "procrastination"
        assert len(analysis.pattern_triggers) == 1
        assert len(analysis.notable_facts) == 1

    def test_mood_score_out_of_range_raises(self):
        """mood_score > 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationAnalysis(
                mood_score=2.0,
                energy_level=0.5,
                focus_score=0.5,
                detected_patterns=[],
                pattern_triggers=[],
                notable_facts=[],
            )

    def test_mood_score_below_range_raises(self):
        """mood_score < -1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationAnalysis(
                mood_score=-1.5,
                energy_level=0.5,
                focus_score=0.5,
            )

    def test_energy_level_out_of_range_raises(self):
        """energy_level > 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationAnalysis(
                mood_score=0.0,
                energy_level=1.5,
                focus_score=0.5,
            )

    def test_energy_level_negative_raises(self):
        """energy_level < 0.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationAnalysis(
                mood_score=0.0,
                energy_level=-0.1,
                focus_score=0.5,
            )

    def test_focus_score_out_of_range_raises(self):
        """focus_score > 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationAnalysis(
                mood_score=0.0,
                energy_level=0.5,
                focus_score=1.1,
            )

    def test_defaults_for_optional_lists(self):
        """Optional list fields should default to empty lists."""
        analysis = ConversationAnalysis(
            mood_score=0.0,
            energy_level=0.5,
            focus_score=0.5,
        )
        assert analysis.detected_patterns == []
        assert analysis.pattern_triggers == []
        assert analysis.notable_facts == []

    def test_boundary_values(self):
        """Boundary values should be accepted."""
        analysis = ConversationAnalysis(
            mood_score=-1.0,
            energy_level=0.0,
            focus_score=1.0,
        )
        assert analysis.mood_score == -1.0
        assert analysis.energy_level == 0.0
        assert analysis.focus_score == 1.0

    def test_multiple_patterns(self):
        """Multiple patterns, triggers, and facts should work."""
        analysis = ConversationAnalysis(
            mood_score=0.0,
            energy_level=0.5,
            focus_score=0.5,
            detected_patterns=["procrastination", "hyperfocus", "time_blindness"],
            pattern_triggers=["deadline_stress", "boring_task"],
            notable_facts=["Arbeitet als Designer", "Hat zwei Kinder"],
        )
        assert len(analysis.detected_patterns) == 3
        assert len(analysis.pattern_triggers) == 2
        assert len(analysis.notable_facts) == 2


# ===========================================================================
# PatternLogResponse
# ===========================================================================

class TestPatternLogResponse:
    """Tests for PatternLogResponse schema."""

    def test_valid_response(self):
        """Valid pattern log response should work."""
        now = datetime.now(timezone.utc)
        log = PatternLogResponse(
            id=uuid4(),
            conversation_id=uuid4(),
            episode_id="ep_123",
            mood_score=0.5,
            energy_level=0.7,
            focus_score=0.3,
            created_at=now,
        )
        assert log.mood_score == 0.5
        assert log.episode_id == "ep_123"
        assert log.created_at == now

    def test_nullable_fields(self):
        """Optional fields should accept None."""
        log = PatternLogResponse(
            id=uuid4(),
            conversation_id=None,
            episode_id=None,
            mood_score=None,
            energy_level=None,
            focus_score=None,
            created_at=datetime.now(timezone.utc),
        )
        assert log.conversation_id is None
        assert log.episode_id is None
        assert log.mood_score is None
        assert log.energy_level is None
        assert log.focus_score is None


# ===========================================================================
# MemoryStatusResponse
# ===========================================================================

class TestMemoryStatusResponse:
    """Tests for MemoryStatusResponse schema."""

    def test_valid_status(self):
        """Valid memory status response should work."""
        status = MemoryStatusResponse(
            enabled=True,
            total_episodes=42,
            total_entities=156,
            last_analysis_at=datetime.now(timezone.utc),
        )
        assert status.enabled is True
        assert status.total_episodes == 42
        assert status.total_entities == 156
        assert status.last_analysis_at is not None

    def test_last_analysis_at_optional(self):
        """last_analysis_at should be optional (None)."""
        status = MemoryStatusResponse(
            enabled=False,
            total_episodes=0,
            total_entities=0,
        )
        assert status.enabled is False
        assert status.last_analysis_at is None


# ===========================================================================
# MemorySettingsUpdate
# ===========================================================================

class TestMemorySettingsUpdate:
    """Tests for MemorySettingsUpdate schema."""

    def test_enable(self):
        """Enable memory setting."""
        update = MemorySettingsUpdate(enabled=True)
        assert update.enabled is True

    def test_disable(self):
        """Disable memory setting."""
        update = MemorySettingsUpdate(enabled=False)
        assert update.enabled is False

    def test_missing_enabled_raises(self):
        """Missing required 'enabled' field should raise ValidationError."""
        with pytest.raises(ValidationError):
            MemorySettingsUpdate()


# ===========================================================================
# MemoryExportResponse
# ===========================================================================

class TestMemoryExportResponse:
    """Tests for MemoryExportResponse (DSGVO Art. 15)."""

    def test_valid_export(self):
        """Valid export response with data."""
        now = datetime.now(timezone.utc)
        export = MemoryExportResponse(
            entities=[{"name": "User", "type": "person"}],
            relations=[{"source": "User", "target": "Task", "type": "works_on"}],
            pattern_logs=[
                PatternLogResponse(
                    id=uuid4(),
                    mood_score=0.5,
                    energy_level=0.7,
                    focus_score=0.3,
                    created_at=now,
                )
            ],
            exported_at=now,
        )
        assert len(export.entities) == 1
        assert len(export.relations) == 1
        assert len(export.pattern_logs) == 1
        assert export.exported_at == now

    def test_empty_export(self):
        """Export with no data should work."""
        export = MemoryExportResponse(
            entities=[],
            relations=[],
            pattern_logs=[],
            exported_at=datetime.now(timezone.utc),
        )
        assert len(export.entities) == 0
        assert len(export.relations) == 0
        assert len(export.pattern_logs) == 0
