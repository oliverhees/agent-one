"""Tests for MemoryService orchestrator.

These tests do NOT require a database -- all DB fixtures from conftest.py
are overridden with no-op versions. Dependencies are fully mocked.
"""

import asyncio
from typing import Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.memory import ConversationAnalysis
from app.services.memory import MemoryService


# ---------------------------------------------------------------------------
# Override DB fixtures from conftest.py
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Override session-scoped event loop for this test module."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clean_tables():
    """No-op override: MemoryService tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: MemoryService tests don't need database setup."""
    yield


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_graphiti():
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
def mock_analysis():
    return ConversationAnalysis(
        mood_score=0.3,
        energy_level=0.6,
        focus_score=0.4,
        detected_patterns=["procrastination"],
        pattern_triggers=["deadline_stress"],
        notable_facts=["User arbeitet als Designer"],
    )


# ===========================================================================
# process_episode
# ===========================================================================


class TestProcessEpisode:
    async def test_calls_graphiti_and_analyzer(
        self, mock_db, mock_graphiti, mock_analysis
    ):
        service = MemoryService(mock_db, mock_graphiti)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(return_value=mock_analysis)

        await service.process_episode(
            str(uuid4()),
            str(uuid4()),
            [{"role": "user", "content": "Ich prokrastiniere"}],
        )

        mock_graphiti.add_episode.assert_called_once()
        service.nlp_analyzer.analyze.assert_called_once()
        mock_db.add.assert_called_once()

    async def test_empty_messages_returns_early(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        await service.process_episode(str(uuid4()), str(uuid4()), [])
        mock_graphiti.add_episode.assert_not_called()

    async def test_graceful_on_graphiti_failure(self, mock_db, mock_analysis):
        failing_graphiti = AsyncMock()
        failing_graphiti.enabled = True
        failing_graphiti.add_episode = AsyncMock(return_value=None)

        service = MemoryService(mock_db, failing_graphiti)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(return_value=mock_analysis)

        # Should not raise
        await service.process_episode(
            str(uuid4()),
            str(uuid4()),
            [{"role": "user", "content": "test"}],
        )

        # NLP analysis should still run even if Graphiti returned None
        service.nlp_analyzer.analyze.assert_called_once()
        mock_db.add.assert_called_once()

    async def test_stores_pattern_log_with_correct_fields(
        self, mock_db, mock_graphiti, mock_analysis
    ):
        service = MemoryService(mock_db, mock_graphiti)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(return_value=mock_analysis)

        user_id = str(uuid4())
        conv_id = str(uuid4())

        await service.process_episode(
            user_id, conv_id,
            [{"role": "user", "content": "test"}],
        )

        # Verify the PatternLog passed to db.add
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.user_id == user_id
        assert added_obj.conversation_id == conv_id
        assert added_obj.episode_id == "episode-uuid-123"
        assert added_obj.mood_score == 0.3
        assert added_obj.energy_level == 0.6
        assert added_obj.focus_score == 0.4

    async def test_formats_messages_for_graphiti(
        self, mock_db, mock_graphiti, mock_analysis
    ):
        service = MemoryService(mock_db, mock_graphiti)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(return_value=mock_analysis)

        await service.process_episode(
            str(uuid4()),
            str(uuid4()),
            [
                {"role": "user", "content": "Hallo"},
                {"role": "assistant", "content": "Hi!"},
            ],
        )

        # Check the content passed to add_episode
        call_kwargs = mock_graphiti.add_episode.call_args
        content = call_kwargs.kwargs.get("content") or call_kwargs[1].get("content", "")
        if not content:
            # positional args: name, content, user_id
            content = call_kwargs[1].get("content", call_kwargs.kwargs.get("content", ""))
        assert "User: Hallo" in content or "ALICE: Hi!" in content


# ===========================================================================
# get_context
# ===========================================================================


class TestGetContext:
    async def test_returns_facts_and_trends(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        service.pattern_analyzer = AsyncMock()
        service.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "avg_mood": 0.3,
            "avg_energy": 0.5,
            "avg_focus": 0.4,
            "total_conversations": 5,
            "mood_trend": "declining",
            "min_mood": 0.1,
            "max_mood": 0.6,
        })

        context = await service.get_context(str(uuid4()), "test query")

        assert "facts" in context
        assert "trends" in context
        assert len(context["facts"]) == 2

    async def test_returns_empty_on_graphiti_error(self, mock_db):
        failing_graphiti = AsyncMock()
        failing_graphiti.enabled = True
        failing_graphiti.search = AsyncMock(side_effect=Exception("connection lost"))

        service = MemoryService(mock_db, failing_graphiti)
        service.pattern_analyzer = AsyncMock()
        service.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "total_conversations": 0,
        })

        context = await service.get_context(str(uuid4()), "test")

        assert context["facts"] == []
        assert context["trends"]["total_conversations"] == 0

    async def test_calls_graphiti_search_with_correct_params(
        self, mock_db, mock_graphiti
    ):
        service = MemoryService(mock_db, mock_graphiti)
        service.pattern_analyzer = AsyncMock()
        service.pattern_analyzer.get_recent_trends = AsyncMock(return_value={
            "total_conversations": 0,
        })

        user_id = str(uuid4())
        await service.get_context(user_id, "meine Arbeit")

        mock_graphiti.search.assert_called_once_with(
            query="meine Arbeit",
            user_id=user_id,
            num_results=10,
        )


# ===========================================================================
# format_context_for_prompt
# ===========================================================================


class TestFormatContext:
    def test_formats_with_facts_and_trends(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        context = {
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
        }
        result = service.format_context_for_prompt(context)
        assert "Was du ueber den User weisst" in result
        assert "Designer" in result
        assert "Verhaltenstrends" in result

    def test_empty_context_returns_empty_string(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        result = service.format_context_for_prompt({
            "facts": [],
            "trends": {"total_conversations": 0},
        })
        assert result == ""

    def test_facts_only(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        context = {
            "facts": [{"fact": "User mag Kaffee"}],
            "trends": {"total_conversations": 0},
        }
        result = service.format_context_for_prompt(context)
        assert "Was du ueber den User weisst" in result
        assert "Kaffee" in result
        assert "Verhaltenstrends" not in result

    def test_trends_only(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        context = {
            "facts": [],
            "trends": {
                "avg_mood": 0.5,
                "avg_energy": 0.5,
                "avg_focus": 0.5,
                "total_conversations": 3,
                "mood_trend": "stable",
                "min_mood": 0.3,
                "max_mood": 0.7,
            },
        }
        result = service.format_context_for_prompt(context)
        assert "Was du ueber den User weisst" not in result
        assert "Verhaltenstrends" in result

    def test_includes_recommendations_when_applicable(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        context = {
            "facts": [],
            "trends": {
                "avg_mood": -0.5,
                "avg_energy": 0.3,
                "avg_focus": 0.1,
                "total_conversations": 10,
                "mood_trend": "declining",
                "min_mood": -0.8,
                "max_mood": 0.1,
            },
        }
        result = service.format_context_for_prompt(context)
        assert "Handlungsempfehlung" in result


# ===========================================================================
# _build_recommendations
# ===========================================================================


class TestRecommendations:
    def test_low_focus_recommendation(self):
        recs = MemoryService._build_recommendations({
            "avg_focus": 0.2,
            "avg_mood": 0.5,
            "mood_trend": "stable",
        })
        assert any("Fokus" in r for r in recs)

    def test_low_mood_recommendation(self):
        recs = MemoryService._build_recommendations({
            "avg_focus": 0.5,
            "avg_mood": -0.3,
            "mood_trend": "stable",
        })
        assert any("empathisch" in r for r in recs)

    def test_declining_mood_recommendation(self):
        recs = MemoryService._build_recommendations({
            "avg_focus": 0.5,
            "avg_mood": 0.5,
            "mood_trend": "declining",
        })
        assert any("fallend" in r for r in recs)

    def test_no_recommendations_when_good(self):
        recs = MemoryService._build_recommendations({
            "avg_focus": 0.5,
            "avg_mood": 0.5,
            "mood_trend": "stable",
        })
        assert recs == []

    def test_multiple_recommendations(self):
        recs = MemoryService._build_recommendations({
            "avg_focus": 0.1,
            "avg_mood": -0.5,
            "mood_trend": "declining",
        })
        assert len(recs) == 3


# ===========================================================================
# get_status
# ===========================================================================


class TestGetStatus:
    async def test_returns_status_dict(self, mock_db, mock_graphiti):
        service = MemoryService(mock_db, mock_graphiti)
        service.pattern_analyzer = AsyncMock()
        service.pattern_analyzer.get_log_count = AsyncMock(return_value=10)
        service.pattern_analyzer.get_last_analysis = AsyncMock(return_value=None)

        status = await service.get_status(str(uuid4()))

        assert status["enabled"] is True
        assert status["total_episodes"] == 10
        assert status["total_entities"] == 42
        assert status["last_analysis_at"] is None

    async def test_status_when_graphiti_disabled(self, mock_db):
        disabled_graphiti = AsyncMock()
        disabled_graphiti.enabled = False
        disabled_graphiti.get_entity_count = AsyncMock(return_value=0)

        service = MemoryService(mock_db, disabled_graphiti)
        service.pattern_analyzer = AsyncMock()
        service.pattern_analyzer.get_log_count = AsyncMock(return_value=0)
        service.pattern_analyzer.get_last_analysis = AsyncMock(return_value=None)

        status = await service.get_status(str(uuid4()))

        assert status["enabled"] is False
        assert status["total_entities"] == 0


# ===========================================================================
# export_user_data
# ===========================================================================


class TestExportUserData:
    async def test_exports_entities_and_logs(self, mock_db, mock_graphiti):
        # Mock DB execute to return pattern logs
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = MemoryService(mock_db, mock_graphiti)

        export = await service.export_user_data(str(uuid4()))

        assert "entities" in export
        assert "relations" in export
        assert "pattern_logs" in export
        assert "exported_at" in export
        # Graphiti search was called with wildcard
        mock_graphiti.search.assert_called_once()


# ===========================================================================
# delete_user_data
# ===========================================================================


class TestDeleteUserData:
    async def test_deletes_graph_and_logs(self, mock_db, mock_graphiti):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = MemoryService(mock_db, mock_graphiti)

        result = await service.delete_user_data(str(uuid4()))

        assert result is True
        mock_graphiti.delete_user_data.assert_called_once()

    async def test_returns_false_on_graph_failure(self, mock_db):
        failing_graphiti = AsyncMock()
        failing_graphiti.enabled = True
        failing_graphiti.delete_user_data = AsyncMock(return_value=False)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = MemoryService(mock_db, failing_graphiti)

        result = await service.delete_user_data(str(uuid4()))

        assert result is False


# ===========================================================================
# _format_messages (internal helper)
# ===========================================================================


class TestFormatMessages:
    def test_formats_user_and_assistant(self):
        messages = [
            {"role": "user", "content": "Hallo"},
            {"role": "assistant", "content": "Hi! Wie geht es dir?"},
            {"role": "user", "content": "Gut, danke."},
        ]
        result = MemoryService._format_messages(messages)
        assert "User: Hallo" in result
        assert "ALICE: Hi! Wie geht es dir?" in result
        assert "User: Gut, danke." in result

    def test_handles_unknown_roles(self):
        messages = [{"role": "system", "content": "You are ALICE."}]
        result = MemoryService._format_messages(messages)
        assert "system: You are ALICE." in result

    def test_empty_messages(self):
        result = MemoryService._format_messages([])
        assert result == ""
