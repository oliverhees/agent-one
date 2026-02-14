"""Tests for GraphitiClient wrapper.

These tests do NOT require a database — all DB fixtures from conftest.py
are overridden with no-op versions.
"""

import asyncio
from typing import Generator

import pytest

from app.services.graphiti_client import GraphitiClient, ADHD_SEED_PATTERNS


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
    """No-op override: GraphitiClient tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: GraphitiClient tests don't need database setup."""
    yield


# ===========================================================================
# ADHD Seed Patterns
# ===========================================================================


class TestADHDSeedPatterns:
    def test_seed_patterns_count(self):
        assert len(ADHD_SEED_PATTERNS) == 13

    def test_seed_patterns_have_required_fields(self):
        for pattern in ADHD_SEED_PATTERNS:
            assert "name" in pattern
            assert "description" in pattern
            assert len(pattern["name"]) > 0
            assert len(pattern["description"]) > 0

    def test_all_expected_patterns_present(self):
        names = {p["name"] for p in ADHD_SEED_PATTERNS}
        expected = {
            "Procrastination", "Hyperfocus", "Task-Switching",
            "Paralysis by Analysis", "Time Blindness",
            "Emotional Dysregulation", "Rejection Sensitivity",
            "Dopamine Seeking", "Working Memory Overload",
            "Sleep Disruption", "Transition Difficulty",
            "Perfectionism Paralysis", "Social Masking",
        }
        assert names == expected


# ===========================================================================
# GraphitiClient — Disabled Mode
# ===========================================================================


class TestGraphitiClientDisabled:
    def test_client_disabled(self):
        client = GraphitiClient(enabled=False)
        assert client.enabled is False

    @pytest.mark.asyncio
    async def test_search_when_disabled_returns_empty(self):
        client = GraphitiClient(enabled=False)
        results = await client.search("test query", user_id="test-user")
        assert results == []

    @pytest.mark.asyncio
    async def test_add_episode_when_disabled_returns_none(self):
        client = GraphitiClient(enabled=False)
        result = await client.add_episode(name="test", content="test content", user_id="test-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_when_disabled_returns_true(self):
        client = GraphitiClient(enabled=False)
        result = await client.delete_user_data("test-user")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_entity_count_when_disabled_returns_zero(self):
        client = GraphitiClient(enabled=False)
        result = await client.get_entity_count("test-user")
        assert result == 0

    @pytest.mark.asyncio
    async def test_seed_when_disabled_does_nothing(self):
        client = GraphitiClient(enabled=False)
        await client.seed_adhd_patterns()  # Should not raise

    @pytest.mark.asyncio
    async def test_initialize_when_disabled_does_nothing(self):
        client = GraphitiClient(enabled=False)
        await client.initialize()
        assert client.enabled is False
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self):
        client = GraphitiClient(enabled=False)
        await client.close()  # Should not raise


# ===========================================================================
# GraphitiClient — Constructor
# ===========================================================================


class TestGraphitiClientConstructor:
    def test_default_values(self):
        client = GraphitiClient()
        assert client.uri == "falkor://localhost:6379"
        assert client.enabled is True
        assert client._client is None
        assert client._initialized is False

    def test_custom_uri(self):
        client = GraphitiClient(uri="falkor://custom:1234", enabled=True)
        assert client.uri == "falkor://custom:1234"
        assert client.enabled is True


# ===========================================================================
# Singleton / get_graphiti_client
# ===========================================================================


class TestGetGraphitiClient:
    def test_returns_disabled_when_none(self):
        from app.services import graphiti_client as mod

        # Ensure the module-level singleton is None
        original = mod.graphiti_client
        mod.graphiti_client = None
        try:
            result = mod.get_graphiti_client()
            assert result.enabled is False
        finally:
            mod.graphiti_client = original

    def test_returns_singleton_when_set(self):
        from app.services import graphiti_client as mod

        original = mod.graphiti_client
        sentinel = GraphitiClient(uri="falkor://test:9999", enabled=True)
        mod.graphiti_client = sentinel
        try:
            result = mod.get_graphiti_client()
            assert result is sentinel
        finally:
            mod.graphiti_client = original
