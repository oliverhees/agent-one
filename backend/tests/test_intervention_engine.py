"""Tests for InterventionEngine — ADHS pattern detection."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.intervention_engine import InterventionEngine, MESSAGES


# Override DB fixtures from conftest.py — these are pure unit tests.
@pytest.fixture
def setup_db():
    """No-op: skip real DB setup for unit tests."""
    yield None


@pytest.fixture(autouse=True)
def clean_tables():
    """No-op: skip real DB cleanup for unit tests."""
    yield


class TestPatternDetection:
    """Tests for _detect_patterns — pure logic, no DB required."""

    def _make_engine(self) -> InterventionEngine:
        """Create an engine instance without DB initialization."""
        return InterventionEngine.__new__(InterventionEngine)

    def test_hyperfocus_detected(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "hyperfocus" in types

    def test_hyperfocus_not_detected_when_normal(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.5, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "hyperfocus" not in types

    def test_hyperfocus_boundary_at_0_9(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.9, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "hyperfocus" not in types, "Focus == 0.9 should NOT trigger (threshold is > 0.9)"

    def test_hyperfocus_message_correct(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3, "total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        hyperfocus = [p for p in patterns if p["type"] == "hyperfocus"][0]
        assert hyperfocus["message"] == MESSAGES["hyperfocus"]

    def test_procrastination_spiral_detected(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.3, "avg_energy": 0.2, "avg_mood": -0.3,
            "total_conversations": 5, "mood_trend": "declining",
        }
        stats = {"tasks_completed": 1, "current_streak": 0}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "procrastination" in types

    def test_procrastination_not_detected_with_good_energy(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.3, "avg_energy": 0.5, "avg_mood": -0.3,
            "total_conversations": 5,
        }
        stats = {"tasks_completed": 1}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "procrastination" not in types

    def test_decision_fatigue_detected(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.2, "avg_energy": 0.4, "avg_mood": 0.0, "total_conversations": 5}
        stats = {"open_tasks": 8}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "decision_fatigue" in types

    def test_decision_fatigue_not_detected_with_few_tasks(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.2, "avg_energy": 0.4, "avg_mood": 0.0, "total_conversations": 5}
        stats = {"open_tasks": 3}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "decision_fatigue" not in types

    def test_energy_crash_detected(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.4, "avg_energy": 0.15, "avg_mood": 0.0, "total_conversations": 5}
        recent_logs = [
            {"energy_level": 0.3},
            {"energy_level": 0.2},
            {"energy_level": 0.1},
        ]
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=recent_logs)
        types = [p["type"] for p in patterns]
        assert "energy_crash" in types

    def test_energy_crash_not_detected_with_rising_energy(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.4, "avg_energy": 0.15, "avg_mood": 0.0, "total_conversations": 5}
        recent_logs = [
            {"energy_level": 0.1},
            {"energy_level": 0.2},
            {"energy_level": 0.3},
        ]
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=recent_logs)
        types = [p["type"] for p in patterns]
        assert "energy_crash" not in types

    def test_energy_crash_needs_low_avg_energy(self):
        engine = self._make_engine()
        trends = {"avg_focus": 0.4, "avg_energy": 0.5, "avg_mood": 0.0, "total_conversations": 5}
        recent_logs = [
            {"energy_level": 0.8},
            {"energy_level": 0.6},
            {"energy_level": 0.4},
        ]
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=recent_logs)
        types = [p["type"] for p in patterns]
        assert "energy_crash" not in types, "avg_energy >= 0.3 should not trigger energy_crash"

    def test_social_masking_detected(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.8, "avg_energy": 0.7, "avg_mood": -0.4,
            "total_conversations": 5, "mood_trend": "declining",
        }
        stats = {"tasks_completed": 15}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "social_masking" in types

    def test_social_masking_not_detected_with_stable_mood(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.8, "avg_energy": 0.7, "avg_mood": -0.4,
            "total_conversations": 5, "mood_trend": "stable",
        }
        stats = {"tasks_completed": 15}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "social_masking" not in types

    def test_sleep_disruption_detected(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.4, "avg_energy": 0.2, "avg_mood": -0.1,
            "total_conversations": 5, "mood_trend": "stable",
        }
        patterns = engine._detect_patterns(trends, stats={"tasks_completed": 5}, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "sleep_disruption" in types

    def test_sleep_disruption_not_triggered_when_energy_crash_present(self):
        """If energy_crash is already detected, sleep_disruption should be suppressed."""
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.4, "avg_energy": 0.15, "avg_mood": -0.1,
            "total_conversations": 5,
        }
        recent_logs = [
            {"energy_level": 0.3},
            {"energy_level": 0.2},
            {"energy_level": 0.1},
        ]
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=recent_logs)
        types = [p["type"] for p in patterns]
        assert "energy_crash" in types
        assert "sleep_disruption" not in types

    def test_no_patterns_when_all_good(self):
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.6, "avg_energy": 0.6, "avg_mood": 0.5,
            "total_conversations": 5, "mood_trend": "stable",
        }
        stats = {"tasks_completed": 10, "current_streak": 5, "open_tasks": 2}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        assert len(patterns) == 0

    def test_multiple_patterns_detected_simultaneously(self):
        """Low energy + low mood + few tasks can trigger both procrastination and sleep_disruption."""
        engine = self._make_engine()
        trends = {
            "avg_focus": 0.4, "avg_energy": 0.2, "avg_mood": -0.3,
            "total_conversations": 5, "mood_trend": "stable",
        }
        stats = {"tasks_completed": 1, "open_tasks": 1}
        patterns = engine._detect_patterns(trends, stats, recent_logs=[])
        types = [p["type"] for p in patterns]
        assert "procrastination" in types
        assert "sleep_disruption" in types

    def test_defaults_used_for_missing_stats_keys(self):
        """Engine should handle empty stats/trends dicts gracefully."""
        engine = self._make_engine()
        trends = {"total_conversations": 5}
        patterns = engine._detect_patterns(trends, stats={}, recent_logs=[])
        # With all defaults (focus=0.5, energy=0.5, mood=0.0), no pattern should trigger
        assert len(patterns) == 0


class TestCreateInterventions:
    """Tests for the evaluate() method — mocked DB interactions."""

    @pytest.mark.asyncio
    async def test_creates_intervention_for_pattern(self):
        db = AsyncMock()
        engine = InterventionEngine(db)
        user_id = str(uuid4())

        engine._detect_patterns = MagicMock(return_value=[
            {"type": "hyperfocus", "trigger": "Focus > 0.9", "message": "Pause!"}
        ])
        engine._has_recent_intervention = AsyncMock(return_value=False)
        engine.pattern_analyzer = AsyncMock()
        engine.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3,
            "total_conversations": 5,
        })
        engine._get_user_stats = AsyncMock(return_value={})
        engine._get_recent_logs = AsyncMock(return_value=[])

        interventions = await engine.evaluate(user_id)
        assert len(interventions) == 1
        assert interventions[0]["type"] == "hyperfocus"
        assert interventions[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_skips_when_no_conversations(self):
        db = AsyncMock()
        engine = InterventionEngine(db)
        user_id = str(uuid4())

        engine.pattern_analyzer = AsyncMock()
        engine.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "total_conversations": 0,
        })
        engine._get_user_stats = AsyncMock(return_value={})
        engine._get_recent_logs = AsyncMock(return_value=[])

        interventions = await engine.evaluate(user_id)
        assert interventions == []

    @pytest.mark.asyncio
    async def test_respects_cooldown(self):
        """If a recent intervention of the same type exists, skip it."""
        db = AsyncMock()
        engine = InterventionEngine(db)
        user_id = str(uuid4())

        engine._detect_patterns = MagicMock(return_value=[
            {"type": "hyperfocus", "trigger": "Focus > 0.9", "message": "Pause!"}
        ])
        engine._has_recent_intervention = AsyncMock(return_value=True)
        engine.pattern_analyzer = AsyncMock()
        engine.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "avg_focus": 0.95, "avg_energy": 0.5, "avg_mood": 0.3,
            "total_conversations": 5,
        })
        engine._get_user_stats = AsyncMock(return_value={})
        engine._get_recent_logs = AsyncMock(return_value=[])

        interventions = await engine.evaluate(user_id)
        assert interventions == []

    @pytest.mark.asyncio
    async def test_creates_multiple_interventions(self):
        db = AsyncMock()
        engine = InterventionEngine(db)
        user_id = str(uuid4())

        engine._detect_patterns = MagicMock(return_value=[
            {"type": "procrastination", "trigger": "test", "message": "msg1"},
            {"type": "sleep_disruption", "trigger": "test2", "message": "msg2"},
        ])
        engine._has_recent_intervention = AsyncMock(return_value=False)
        engine.pattern_analyzer = AsyncMock()
        engine.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "total_conversations": 5,
        })
        engine._get_user_stats = AsyncMock(return_value={})
        engine._get_recent_logs = AsyncMock(return_value=[])

        interventions = await engine.evaluate(user_id)
        assert len(interventions) == 2
        types = [i["type"] for i in interventions]
        assert "procrastination" in types
        assert "sleep_disruption" in types
