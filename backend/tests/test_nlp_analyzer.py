"""Tests for NLPAnalyzer service."""

import asyncio
import json
from typing import Generator

import pytest

from app.schemas.memory import ConversationAnalysis
from app.services.nlp_analyzer import NLPAnalyzer


# ---------------------------------------------------------------------------
# Override DB fixtures from conftest.py — these tests are pure unit tests
# and do not need a database connection.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Override conftest event_loop for standalone async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clean_tables():
    """No-op override: NLP analyzer tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: NLP analyzer tests don't need database setup."""
    yield


# ===========================================================================
# Tests
# ===========================================================================

class TestNLPAnalyzer:
    """Tests for NLPAnalyzer service."""

    def test_build_analysis_prompt_contains_fields(self):
        """Prompt should contain all required analysis field names."""
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

    def test_format_messages(self):
        """Messages should be formatted with User/ALICE prefixes."""
        analyzer = NLPAnalyzer()
        messages = [
            {"role": "user", "content": "Hallo"},
            {"role": "assistant", "content": "Hi!"},
        ]
        formatted = analyzer._format_messages(messages)
        assert "User: Hallo" in formatted
        assert "ALICE: Hi!" in formatted

    def test_format_messages_empty(self):
        """Empty message list should return empty string."""
        analyzer = NLPAnalyzer()
        formatted = analyzer._format_messages([])
        assert formatted == ""

    def test_format_messages_unknown_role(self):
        """Unknown roles should use the role name as prefix."""
        analyzer = NLPAnalyzer()
        messages = [{"role": "system", "content": "System message"}]
        formatted = analyzer._format_messages(messages)
        assert "system: System message" in formatted

    def test_parse_valid_json(self):
        """Valid JSON should parse into ConversationAnalysis."""
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

    def test_parse_json_with_markdown_code_block(self):
        """JSON wrapped in markdown code blocks should parse correctly."""
        analyzer = NLPAnalyzer()
        raw = (
            '```json\n'
            '{"mood_score": 0.5, "energy_level": 0.6, "focus_score": 0.7, '
            '"detected_patterns": [], "pattern_triggers": [], "notable_facts": []}\n'
            '```'
        )
        result = analyzer._parse_response(raw)
        assert result.mood_score == 0.5

    def test_parse_json_with_plain_code_block(self):
        """JSON wrapped in plain code blocks (no language tag) should parse."""
        analyzer = NLPAnalyzer()
        raw = (
            '```\n'
            '{"mood_score": 0.2, "energy_level": 0.3, "focus_score": 0.4, '
            '"detected_patterns": ["hyperfocus"], "pattern_triggers": [], '
            '"notable_facts": []}\n'
            '```'
        )
        result = analyzer._parse_response(raw)
        assert result.mood_score == 0.2
        assert result.detected_patterns == ["hyperfocus"]

    def test_parse_invalid_json_returns_neutral(self):
        """Invalid JSON should return neutral ConversationAnalysis."""
        analyzer = NLPAnalyzer()
        result = analyzer._parse_response("not json at all")
        assert isinstance(result, ConversationAnalysis)
        assert result.mood_score == 0.0
        assert result.energy_level == 0.5
        assert result.focus_score == 0.5
        assert result.detected_patterns == []

    def test_parse_out_of_range_values_returns_neutral(self):
        """Values outside valid ranges should return neutral analysis."""
        analyzer = NLPAnalyzer()
        raw = json.dumps({
            "mood_score": 5.0,  # out of range
            "energy_level": 0.5,
            "focus_score": 0.5,
            "detected_patterns": [],
            "pattern_triggers": [],
            "notable_facts": [],
        })
        result = analyzer._parse_response(raw)
        # Pydantic validation should fail, returning neutral
        assert result.mood_score == 0.0
        assert result.energy_level == 0.5

    def test_parse_empty_string_returns_neutral(self):
        """Empty string should return neutral analysis."""
        analyzer = NLPAnalyzer()
        result = analyzer._parse_response("")
        assert result.mood_score == 0.0

    @pytest.mark.asyncio
    async def test_analyze_empty_messages_returns_neutral(self):
        """Empty message list should immediately return neutral values."""
        analyzer = NLPAnalyzer()
        result = await analyzer.analyze([])
        assert result.mood_score == 0.0
        assert result.detected_patterns == []

    @pytest.mark.asyncio
    async def test_analyze_no_api_key_returns_neutral(self):
        """Missing API key should immediately return neutral values."""
        analyzer = NLPAnalyzer()
        analyzer.api_key = ""
        result = await analyzer.analyze([{"role": "user", "content": "test"}])
        assert result.mood_score == 0.0

    def test_model_is_haiku(self):
        """Analyzer should use the fast/cheap Haiku model."""
        analyzer = NLPAnalyzer()
        assert "haiku" in analyzer.model

    def test_build_prompt_includes_conversation_content(self):
        """The built prompt should include actual message content."""
        analyzer = NLPAnalyzer()
        messages = [
            {"role": "user", "content": "Ich habe heute Probleme mit Zeitmanagement"},
        ]
        prompt = analyzer._build_analysis_prompt(messages)
        assert "Zeitmanagement" in prompt
        assert "User:" in prompt
