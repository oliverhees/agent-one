"""Tests for ContextBuilder.

These tests do NOT require a database -- all DB fixtures from conftest.py
are overridden with no-op versions. Dependencies are fully mocked.
"""

import asyncio
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.context_builder import ContextBuilder


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
    """No-op override: ContextBuilder tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: ContextBuilder tests don't need database setup."""
    yield


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_memory_service():
    service = MagicMock()
    service.get_context = AsyncMock(return_value={
        "facts": [
            {"fact": "User arbeitet als Designer"},
            {"fact": "User hat Schwester Lisa"},
        ],
        "trends": {
            "avg_mood": 0.3, "avg_energy": 0.5, "avg_focus": 0.2,
            "total_conversations": 5, "mood_trend": "declining",
            "min_mood": 0.1, "max_mood": 0.6,
        },
    })
    service.format_context_for_prompt = MagicMock(return_value=(
        "## Was du ueber den User weisst:\n"
        "- User arbeitet als Designer\n"
        "- User hat Schwester Lisa\n\n"
        "## Aktuelle Verhaltenstrends:\n"
        "Fokus niedrig, Stimmung fallend"
    ))
    return service


# ===========================================================================
# enrich
# ===========================================================================


class TestContextBuilder:
    async def test_enrich_adds_memory_block(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        base = "Du bist ALICE, ein ADHS-Coach."
        enriched = await builder.enrich(base, "user-1", "Ich kann mich nicht konzentrieren")
        assert "Du bist ALICE" in enriched
        assert "Was du ueber den User weisst" in enriched
        assert "Designer" in enriched

    async def test_enrich_without_memory_returns_base(self):
        service = MagicMock()
        service.get_context = AsyncMock(return_value={
            "facts": [], "trends": {"total_conversations": 0},
        })
        service.format_context_for_prompt = MagicMock(return_value="")
        builder = ContextBuilder(service)
        result = await builder.enrich("Base prompt", "user-1", "Hallo")
        assert result == "Base prompt"

    async def test_enrich_graceful_on_failure(self):
        service = MagicMock()
        service.get_context = AsyncMock(side_effect=Exception("DB down"))
        builder = ContextBuilder(service)
        result = await builder.enrich("Base prompt", "user-1", "test")
        assert result == "Base prompt"

    async def test_enrich_calls_get_context_with_correct_args(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        await builder.enrich("base", "user-42", "my query")
        mock_memory_service.get_context.assert_called_once_with(
            user_id="user-42", query="my query",
        )

    async def test_enrich_calls_format_context_for_prompt(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        await builder.enrich("base", "user-1", "test")
        mock_memory_service.format_context_for_prompt.assert_called_once()

    async def test_enrich_preserves_base_prompt_at_start(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        base = "Du bist ALICE."
        enriched = await builder.enrich(base, "user-1", "test")
        assert enriched.startswith(base)

    async def test_enrich_separates_base_and_memory_with_blank_lines(self, mock_memory_service):
        builder = ContextBuilder(mock_memory_service)
        base = "Du bist ALICE."
        enriched = await builder.enrich(base, "user-1", "test")
        assert "\n\n" in enriched

    async def test_enrich_graceful_on_format_failure(self):
        service = MagicMock()
        service.get_context = AsyncMock(return_value={"facts": [], "trends": {}})
        service.format_context_for_prompt = MagicMock(side_effect=Exception("format error"))
        builder = ContextBuilder(service)
        result = await builder.enrich("Base prompt", "user-1", "test")
        assert result == "Base prompt"
