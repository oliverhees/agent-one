"""End-to-end integration tests for the ALICE memory system pipeline.

These tests use the REAL database (test DB) to verify the full pipeline:
  chat messages -> process_episode -> pattern_log (DB) -> get_context -> enriched prompt

NLPAnalyzer is mocked to avoid real Claude API calls.
GraphitiClient uses enabled=False mode (built-in no-op).
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.pattern_log import PatternLog
from app.models.user import User
from app.schemas.memory import ConversationAnalysis
from app.services.context_builder import ContextBuilder
from app.services.graphiti_client import GraphitiClient
from app.services.memory import MemoryService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# I1: Pre-computed bcrypt hash for "TestPassword123" to avoid hashing on every fixture call.
_STATIC_PASSWORD_HASH = "$2b$12$LJ3m4ys3Lk0TSwHBQWCpAOTSs2rjBnBf3FkhsFKvqseOlkEMKJDMy"


def _make_analysis(
    mood: float = 0.3,
    energy: float = 0.6,
    focus: float = 0.4,
    patterns: list[str] | None = None,
    triggers: list[str] | None = None,
    facts: list[str] | None = None,
) -> ConversationAnalysis:
    """Create a ConversationAnalysis with sensible defaults."""
    return ConversationAnalysis(
        mood_score=mood,
        energy_level=energy,
        focus_score=focus,
        detected_patterns=patterns or ["procrastination"],
        pattern_triggers=triggers or ["deadline_stress"],
        notable_facts=facts or ["User arbeitet als Designer"],
    )


# I6: Immutable tuple instead of mutable module-level list.
SAMPLE_MESSAGES = (
    {"role": "user", "content": "Ich prokrastiniere schon wieder mit dem Kundenprojekt."},
    {"role": "assistant", "content": "Das klingt frustrierend. Was genau blockiert dich?"},
    {"role": "user", "content": "Die Deadline ist Freitag und ich weiss nicht wo ich anfangen soll."},
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_user_row(test_db: AsyncSession) -> User:
    """Create a minimal User row directly in the test database."""
    user = User(
        email=f"e2e-{uuid4().hex[:8]}@test.local",
        password_hash=_STATIC_PASSWORD_HASH,
        display_name="E2E Test User",
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    return user


@pytest_asyncio.fixture
async def conversation_row(test_db: AsyncSession, test_user_row: User) -> Conversation:
    """Create a minimal Conversation row for FK references."""
    conv = Conversation(
        user_id=test_user_row.id,
        title="E2E test conversation",
    )
    test_db.add(conv)
    await test_db.flush()
    return conv


# I3: Synchronous fixtures use @pytest.fixture, not @pytest_asyncio.fixture.
@pytest.fixture
def graphiti_disabled() -> GraphitiClient:
    """Return a disabled GraphitiClient (no FalkorDB needed)."""
    return GraphitiClient(enabled=False)


@pytest.fixture
def mock_nlp_analysis() -> ConversationAnalysis:
    """Default mock analysis result."""
    return _make_analysis()


# ===========================================================================
# Test 1: Full Memory Pipeline
# ===========================================================================


class TestFullMemoryPipeline:
    """Verify the complete flow: process_episode -> pattern_log -> get_context -> prompt."""

    @pytest.mark.asyncio
    async def test_full_pipeline(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        conversation_row: Conversation,
        graphiti_disabled: GraphitiClient,
        mock_nlp_analysis: ConversationAnalysis,
    ):
        user_id = str(test_user_row.id)
        conv_id = str(conversation_row.id)

        # 1. Create MemoryService with disabled Graphiti
        service = MemoryService(test_db, graphiti_disabled)

        # 2. Mock the NLPAnalyzer to return predictable results
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(return_value=mock_nlp_analysis)

        # 3. Process a conversation episode
        await service.process_episode(
            user_id=user_id,
            conversation_id=conv_id,
            messages=SAMPLE_MESSAGES,
        )
        # I5: Explicit commit to verify data persists beyond flush.
        await test_db.commit()

        # 4. Verify pattern_log was created in DB
        stmt = select(PatternLog).where(PatternLog.user_id == user_id)
        result = await test_db.execute(stmt)
        logs = result.scalars().all()

        assert len(logs) == 1
        log = logs[0]
        assert log.conversation_id == conversation_row.id
        assert log.mood_score == pytest.approx(0.3)
        assert log.energy_level == pytest.approx(0.6)
        assert log.focus_score == pytest.approx(0.4)
        # episode_id is None because GraphitiClient is disabled
        assert log.episode_id is None

        # 5. Get memory context
        context = await service.get_context(user_id=user_id, query="Prokrastination")

        assert "facts" in context
        assert "trends" in context
        # With Graphiti disabled, facts should be empty
        assert context["facts"] == []
        # Trends should reflect the one pattern_log we just stored
        assert context["trends"]["total_conversations"] == 1
        assert context["trends"]["avg_mood"] == pytest.approx(0.3, abs=0.01)
        assert context["trends"]["avg_energy"] == pytest.approx(0.6, abs=0.01)
        assert context["trends"]["avg_focus"] == pytest.approx(0.4, abs=0.01)

        # 6. Format for prompt
        prompt_section = service.format_context_for_prompt(context)

        assert isinstance(prompt_section, str)
        assert len(prompt_section) > 0
        assert "Verhaltenstrends" in prompt_section

    @pytest.mark.asyncio
    async def test_empty_messages_skip_processing(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        graphiti_disabled: GraphitiClient,
    ):
        """process_episode with empty messages should create NO pattern_log."""
        service = MemoryService(test_db, graphiti_disabled)
        service.nlp_analyzer = AsyncMock()

        await service.process_episode(
            user_id=str(test_user_row.id),
            conversation_id=str(uuid4()),
            messages=[],
        )

        stmt = select(PatternLog).where(PatternLog.user_id == str(test_user_row.id))
        result = await test_db.execute(stmt)
        assert result.scalars().all() == []
        service.nlp_analyzer.analyze.assert_not_called()


# ===========================================================================
# Test 2: Multiple Episodes Build Trends
# ===========================================================================


class TestMultipleEpisodesTrends:
    """Process multiple episodes and verify PatternAnalyzer detects trends."""

    @pytest.mark.asyncio
    async def test_trends_aggregate_across_episodes(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        conversation_row: Conversation,
        graphiti_disabled: GraphitiClient,
    ):
        user_id = str(test_user_row.id)
        service = MemoryService(test_db, graphiti_disabled)

        # Process 3 episodes with declining mood
        analyses = [
            _make_analysis(mood=0.8, energy=0.7, focus=0.6),
            _make_analysis(mood=0.4, energy=0.5, focus=0.4),
            _make_analysis(mood=-0.2, energy=0.3, focus=0.2),
        ]

        for i, analysis in enumerate(analyses):
            service.nlp_analyzer = AsyncMock()
            service.nlp_analyzer.analyze = AsyncMock(return_value=analysis)
            await service.process_episode(
                user_id=user_id,
                conversation_id=str(conversation_row.id),
                messages=[{"role": "user", "content": f"Episode {i+1}"}],
            )
        # I5: Explicit commit to verify data persists beyond flush.
        await test_db.commit()

        # Verify 3 logs in DB
        stmt = select(PatternLog).where(PatternLog.user_id == user_id)
        result = await test_db.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) == 3

        # Get trends -- should average across all 3
        context = await service.get_context(user_id=user_id, query="Stimmung")
        trends = context["trends"]

        assert trends["total_conversations"] == 3
        # Average mood: (0.8 + 0.4 + (-0.2)) / 3 = 0.333...
        assert trends["avg_mood"] == pytest.approx(0.33, abs=0.05)
        # Average energy: (0.7 + 0.5 + 0.3) / 3 = 0.5
        assert trends["avg_energy"] == pytest.approx(0.5, abs=0.05)
        # Average focus: (0.6 + 0.4 + 0.2) / 3 = 0.4
        assert trends["avg_focus"] == pytest.approx(0.4, abs=0.05)
        # Min/max mood
        assert trends["min_mood"] == pytest.approx(-0.2, abs=0.01)
        assert trends["max_mood"] == pytest.approx(0.8, abs=0.01)

    @pytest.mark.asyncio
    async def test_format_prompt_includes_recommendations_for_low_focus(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        conversation_row: Conversation,
        graphiti_disabled: GraphitiClient,
    ):
        """When avg focus is below 0.3, recommendations should mention Fokus-Techniken."""
        user_id = str(test_user_row.id)
        service = MemoryService(test_db, graphiti_disabled)

        # Store episodes with low focus
        for _ in range(3):
            analysis = _make_analysis(mood=-0.3, energy=0.3, focus=0.1)
            service.nlp_analyzer = AsyncMock()
            service.nlp_analyzer.analyze = AsyncMock(return_value=analysis)
            await service.process_episode(
                user_id=user_id,
                conversation_id=str(conversation_row.id),
                messages=[{"role": "user", "content": "Kann mich nicht konzentrieren"}],
            )
        # I5: Explicit commit to verify data persists beyond flush.
        await test_db.commit()

        context = await service.get_context(user_id=user_id, query="Fokus")
        prompt_section = service.format_context_for_prompt(context)

        assert "Handlungsempfehlung" in prompt_section
        assert "Fokus" in prompt_section


# ===========================================================================
# Test 3: ContextBuilder Enrichment E2E
# ===========================================================================


class TestContextBuilderE2E:
    """Test ContextBuilder enriches a base system prompt with real DB data."""

    @pytest.mark.asyncio
    async def test_enrich_with_real_data(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        conversation_row: Conversation,
        graphiti_disabled: GraphitiClient,
    ):
        user_id = str(test_user_row.id)

        # Set up MemoryService and store an episode
        service = MemoryService(test_db, graphiti_disabled)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(
            return_value=_make_analysis(mood=0.5, energy=0.7, focus=0.8)
        )

        await service.process_episode(
            user_id=user_id,
            conversation_id=str(conversation_row.id),
            messages=SAMPLE_MESSAGES,
        )
        # I5: Explicit commit to verify data persists beyond flush.
        await test_db.commit()

        # Use ContextBuilder to enrich a base prompt
        builder = ContextBuilder(service)
        base_prompt = "Du bist ALICE, ein empathischer ADHS-Coach."

        enriched = await builder.enrich(
            base_prompt=base_prompt,
            user_id=user_id,
            user_message="Ich kann mich heute nicht konzentrieren.",
        )

        # The enriched prompt should start with the base prompt
        assert enriched.startswith(base_prompt)
        # And contain memory context
        assert "Verhaltenstrends" in enriched
        assert "1 Gespraechen" in enriched or "1 Gesprae" in enriched

    @pytest.mark.asyncio
    async def test_enrich_returns_base_when_no_data(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        graphiti_disabled: GraphitiClient,
    ):
        """With no episodes stored, ContextBuilder should return the base prompt."""
        service = MemoryService(test_db, graphiti_disabled)
        builder = ContextBuilder(service)

        base_prompt = "Du bist ALICE."
        enriched = await builder.enrich(
            base_prompt=base_prompt,
            user_id=str(test_user_row.id),
            user_message="Hallo",
        )

        assert enriched == base_prompt


# ===========================================================================
# Test 4: Memory Status Endpoint Integration
# ===========================================================================


class TestMemoryStatusEndpoint:
    """Test GET /api/v1/memory/status via the real HTTP stack."""

    @pytest.mark.asyncio
    async def test_status_returns_valid_data(
        self,
        authenticated_client,
        test_user,
    ):
        response = await authenticated_client.get("/api/v1/memory/status")
        assert response.status_code == 200

        data = response.json()
        assert "enabled" in data
        assert "total_episodes" in data
        assert "total_entities" in data
        assert "last_analysis_at" in data
        assert isinstance(data["enabled"], bool)
        assert isinstance(data["total_episodes"], int)
        assert isinstance(data["total_entities"], int)

    @pytest.mark.asyncio
    async def test_status_unauthenticated(self, client):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/memory/status")
        assert response.status_code in (401, 403)


# ===========================================================================
# Test 5: Memory Export Endpoint Integration
# ===========================================================================


class TestMemoryExportEndpoint:
    """Test GET /api/v1/memory/export via the real HTTP stack."""

    @pytest.mark.asyncio
    async def test_export_returns_empty_when_no_data(
        self,
        authenticated_client,
        test_user,
    ):
        response = await authenticated_client.get("/api/v1/memory/export")
        assert response.status_code == 200

        data = response.json()
        assert "entities" in data
        assert "relations" in data
        assert "pattern_logs" in data
        assert "exported_at" in data
        assert data["pattern_logs"] == []

    @pytest.mark.asyncio
    async def test_export_contains_pattern_logs_after_processing(
        self,
        authenticated_client,
        test_user,
        test_db: AsyncSession,
    ):
        """After inserting a PatternLog via test_db, export should contain data.

        C2: Uses the test_db fixture instead of importing async_session_factory
        from app.core.database (which could target the production database).
        I4: No conditional logic -- data is inserted directly and asserted.
        """
        user_data, access_token, _ = test_user

        # Insert a PatternLog directly via the test database session.
        pattern_log = PatternLog(
            user_id=user_data["id"],
            conversation_id=str(uuid4()),
            mood_score=0.2,
            energy_level=0.5,
            focus_score=0.3,
        )
        test_db.add(pattern_log)
        await test_db.commit()

        # Now the export endpoint should return data
        response = await authenticated_client.get("/api/v1/memory/export")
        assert response.status_code == 200

        data = response.json()
        assert len(data["pattern_logs"]) >= 1
        log = data["pattern_logs"][0]
        assert "mood_score" in log
        assert "energy_level" in log
        assert "focus_score" in log

    @pytest.mark.asyncio
    async def test_export_unauthenticated(self, client):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/memory/export")
        assert response.status_code in (401, 403)


# ===========================================================================
# Test 6: Delete Endpoint Integration
# ===========================================================================


class TestMemoryDeleteEndpoint:
    """Test DELETE /api/v1/memory via the real HTTP stack."""

    @pytest.mark.asyncio
    async def test_delete_returns_success(
        self,
        authenticated_client,
        test_user,
    ):
        response = await authenticated_client.delete("/api/v1/memory")
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert data["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_unauthenticated(self, client):
        """Unauthenticated requests should be rejected."""
        response = await client.delete("/api/v1/memory")
        assert response.status_code in (401, 403)


# ===========================================================================
# Test 7: DSGVO Full Cycle (process -> export -> delete -> verify empty)
# ===========================================================================


class TestDSGVOFullCycle:
    """Verify the full DSGVO lifecycle: store -> export -> delete -> verify."""

    @pytest.mark.asyncio
    async def test_process_export_delete_cycle(
        self,
        test_db: AsyncSession,
        test_user_row: User,
        conversation_row: Conversation,
        graphiti_disabled: GraphitiClient,
    ):
        user_id = str(test_user_row.id)

        # 1. Process an episode
        service = MemoryService(test_db, graphiti_disabled)
        service.nlp_analyzer = AsyncMock()
        service.nlp_analyzer.analyze = AsyncMock(
            return_value=_make_analysis()
        )

        await service.process_episode(
            user_id=user_id,
            conversation_id=str(conversation_row.id),
            messages=SAMPLE_MESSAGES,
        )
        # I5: Explicit commit to verify data persists beyond flush.
        await test_db.commit()

        # 2. Export should contain data
        export = await service.export_user_data(user_id)
        assert len(export["pattern_logs"]) == 1

        # 3. Get status should show 1 episode
        status = await service.get_status(user_id)
        assert status["total_episodes"] == 1
        assert status["last_analysis_at"] is not None

        # 4. Delete user data
        deleted = await service.delete_user_data(user_id)
        assert deleted is True

        # 5. Export should now be empty
        export_after = await service.export_user_data(user_id)
        assert len(export_after["pattern_logs"]) == 0

        # 6. Status should show 0 episodes
        status_after = await service.get_status(user_id)
        assert status_after["total_episodes"] == 0
        assert status_after["last_analysis_at"] is None
