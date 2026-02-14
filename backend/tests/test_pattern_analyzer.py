"""Tests for PatternAnalyzer service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.pattern_analyzer import PatternAnalyzer


# Override DB fixtures from conftest.py — these are pure unit tests.
@pytest.fixture
def setup_db():
    """No-op: skip real DB setup for unit tests."""
    yield None


@pytest.fixture(autouse=True)
def clean_tables():
    """No-op: skip real DB cleanup for unit tests."""
    yield


class TestPatternAnalyzerFormatting:
    """Tests for formatting methods (no DB needed)."""

    def test_format_for_prompt_with_data(self):
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "avg_mood": 0.2,
            "avg_energy": 0.5,
            "avg_focus": 0.3,
            "total_conversations": 5,
            "mood_trend": "declining",
            "min_mood": 0.1,
            "max_mood": 0.6,
        }
        text = analyzer.format_for_prompt(trends)
        assert "5 Gespraechen" in text
        assert "Stimmung" in text
        assert "fallend" in text

    def test_format_for_prompt_no_data(self):
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "total_conversations": 0,
            "avg_mood": 0,
            "avg_energy": 0,
            "avg_focus": 0,
            "mood_trend": "stable",
            "min_mood": 0,
            "max_mood": 0,
        }
        text = analyzer.format_for_prompt(trends)
        assert "keine Verhaltensdaten" in text

    def test_format_for_prompt_rising_trend(self):
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "avg_mood": 0.7,
            "avg_energy": 0.8,
            "avg_focus": 0.9,
            "total_conversations": 10,
            "mood_trend": "rising",
            "min_mood": 0.3,
            "max_mood": 0.9,
        }
        text = analyzer.format_for_prompt(trends)
        assert "steigend" in text
        assert "positiv" in text
        assert "hoch" in text

    def test_format_for_prompt_stable_trend(self):
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "avg_mood": 0.0,
            "avg_energy": 0.5,
            "avg_focus": 0.5,
            "total_conversations": 3,
            "mood_trend": "stable",
            "min_mood": -0.1,
            "max_mood": 0.1,
        }
        text = analyzer.format_for_prompt(trends)
        assert "stabil" in text
        assert "neutral" in text

    def test_score_label_mood(self):
        assert PatternAnalyzer._score_label(0.8, is_mood=True) == "positiv"
        assert PatternAnalyzer._score_label(0.5, is_mood=True) == "positiv"
        assert PatternAnalyzer._score_label(0.3, is_mood=True) == "leicht positiv"
        assert PatternAnalyzer._score_label(0.1, is_mood=True) == "leicht positiv"
        assert PatternAnalyzer._score_label(0.0, is_mood=True) == "neutral"
        assert PatternAnalyzer._score_label(-0.05, is_mood=True) == "neutral"
        assert PatternAnalyzer._score_label(-0.3, is_mood=True) == "leicht negativ"
        assert PatternAnalyzer._score_label(-0.5, is_mood=True) == "leicht negativ"
        assert PatternAnalyzer._score_label(-0.8, is_mood=True) == "negativ"
        assert PatternAnalyzer._score_label(-0.51, is_mood=True) == "negativ"

    def test_score_label_generic(self):
        assert PatternAnalyzer._score_label(0.8) == "hoch"
        assert PatternAnalyzer._score_label(0.7) == "hoch"
        assert PatternAnalyzer._score_label(0.5) == "mittel"
        assert PatternAnalyzer._score_label(0.4) == "mittel"
        assert PatternAnalyzer._score_label(0.2) == "niedrig"
        assert PatternAnalyzer._score_label(0.0) == "niedrig"

    def test_score_label_boundary_values(self):
        """Test exact boundary values for score labels."""
        # Mood boundaries
        assert PatternAnalyzer._score_label(0.5, is_mood=True) == "positiv"
        assert PatternAnalyzer._score_label(0.49, is_mood=True) == "leicht positiv"
        assert PatternAnalyzer._score_label(0.1, is_mood=True) == "leicht positiv"
        assert PatternAnalyzer._score_label(0.09, is_mood=True) == "neutral"
        assert PatternAnalyzer._score_label(-0.1, is_mood=True) == "neutral"
        assert PatternAnalyzer._score_label(-0.11, is_mood=True) == "leicht negativ"
        assert PatternAnalyzer._score_label(-0.5, is_mood=True) == "leicht negativ"
        assert PatternAnalyzer._score_label(-0.51, is_mood=True) == "negativ"

        # Generic boundaries
        assert PatternAnalyzer._score_label(0.7) == "hoch"
        assert PatternAnalyzer._score_label(0.69) == "mittel"
        assert PatternAnalyzer._score_label(0.4) == "mittel"
        assert PatternAnalyzer._score_label(0.39) == "niedrig"

    def test_format_for_prompt_contains_all_sections(self):
        """Ensure format_for_prompt includes mood, energy, and focus lines."""
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "avg_mood": 0.4,
            "avg_energy": 0.6,
            "avg_focus": 0.2,
            "total_conversations": 7,
            "mood_trend": "rising",
            "min_mood": 0.1,
            "max_mood": 0.8,
        }
        text = analyzer.format_for_prompt(trends)
        assert "Stimmung: 0.4" in text
        assert "Energie: 0.6" in text
        assert "Fokus: 0.2" in text
        assert "7 Gespraechen" in text

    def test_format_for_prompt_unknown_trend(self):
        """Test that an unknown mood_trend value maps to 'unbekannt'."""
        analyzer = PatternAnalyzer(db=MagicMock())
        trends = {
            "avg_mood": 0.1,
            "avg_energy": 0.5,
            "avg_focus": 0.5,
            "total_conversations": 2,
            "mood_trend": "unknown_value",
            "min_mood": 0.0,
            "max_mood": 0.2,
        }
        text = analyzer.format_for_prompt(trends)
        assert "unbekannt" in text
