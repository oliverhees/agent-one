"""Tests for PredictionEngine service."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog
from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.user import User
from app.services.prediction_engine import PredictionEngine


@pytest.fixture
async def db_session(test_db: AsyncSession) -> AsyncSession:
    """Provide a test database session."""
    return test_db


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user directly in the database."""
    from app.core.security import hash_password

    user = User(
        email=f"testuser_{uuid4()}@example.com",
        password_hash=hash_password("TestPassword123"),
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


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

        # Create high energy baseline for 30 days ago
        for i in range(10):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.9,
                focus_score=0.8,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=30 - i)
            await db_session.flush()

        # First half: moderate energy (7 days ago to 4 days ago)
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.5,
                focus_score=0.4,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=6 - i)
            await db_session.flush()

        # Second half: very low energy with declining focus (3 days ago to now)
        for i in range(4):
            log = PatternLog(
                user_id=test_user.id,
                mood_score=0.0,
                energy_level=0.2,
                focus_score=0.2,
            )
            db_session.add(log)
            await db_session.flush()
            log.created_at = now - timedelta(days=2 - i)
            await db_session.flush()

        await db_session.commit()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        types = [r["pattern_type"] for r in results]
        assert "energy_crash" in types

    @pytest.mark.asyncio
    async def test_predict_respects_confidence_threshold(self, db_session, test_user):
        """Predictions below 0.6 confidence should not be returned."""
        now = datetime.now(timezone.utc)

        # Create minimal data that might trigger low-confidence predictions
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

        await db_session.commit()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        for r in results:
            assert r["confidence"] >= 0.6

    @pytest.mark.asyncio
    async def test_predict_cooldown_prevents_duplicates(self, db_session, test_user):
        """Should not create duplicate prediction within 24h cooldown."""
        # Create an existing prediction within cooldown period
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
        await db_session.commit()

        # Create conditions that would normally trigger energy_crash
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

        await db_session.commit()

        engine = PredictionEngine(db_session)
        results = await engine.predict(str(test_user.id))

        energy_crash_count = sum(1 for r in results if r["pattern_type"] == "energy_crash")
        assert energy_crash_count == 0

    @pytest.mark.asyncio
    async def test_predict_with_graphiti_enrichment(self, db_session, test_user):
        """Should add graphiti_context when client is available."""
        now = datetime.now(timezone.utc)

        # Create high energy first half
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

        # Create low energy second half
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

        await db_session.commit()

        mock_graphiti = MagicMock()
        mock_graphiti.enabled = True
        mock_graphiti.search = AsyncMock(return_value=[
            {"fact": "User hat abends oft Energieprobleme", "valid_at": None}
        ])

        engine = PredictionEngine(db_session, graphiti_client=mock_graphiti)
        results = await engine.predict(str(test_user.id))

        enriched = [r for r in results if r.get("graphiti_context", {}).get("related_facts")]
        if results:
            assert len(enriched) > 0

    @pytest.mark.asyncio
    async def test_predict_graceful_without_graphiti(self, db_session, test_user):
        """Should work fine without Graphiti client."""
        now = datetime.now(timezone.utc)

        # Create high energy first half
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

        # Create low energy second half
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

        await db_session.commit()

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
        await db_session.commit()

        engine = PredictionEngine(db_session)
        expired_count = await engine.expire_old_predictions(str(test_user.id))

        assert expired_count == 1

        await db_session.refresh(old)
        assert old.status == PredictionStatus.EXPIRED
