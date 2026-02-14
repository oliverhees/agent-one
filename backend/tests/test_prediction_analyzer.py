"""Tests for extended PatternAnalyzer with multi-metric trends."""
import pytest
from datetime import datetime, timedelta, timezone

from app.models.pattern_log import PatternLog
from app.models.user import User
from app.services.pattern_analyzer import PatternAnalyzer


class TestMultiMetricTrends:
    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_returns_all_trends(self, test_db):
        """Should return trend direction for energy and focus, not just mood."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )
        test_db.add(user)
        await test_db.flush()

        now = datetime.now(timezone.utc)
        # Create declining energy pattern: high early, low recently
        for i in range(6):
            log = PatternLog(
                user_id=user.id,
                mood_score=0.5,
                energy_level=0.8 - (i * 0.1),
                focus_score=0.3 + (i * 0.1),
            )
            test_db.add(log)
            await test_db.flush()
            log.created_at = now - timedelta(days=6 - i)
            await test_db.flush()

        analyzer = PatternAnalyzer(test_db)
        trends = await analyzer.get_multi_metric_trends(str(user.id), days=7)

        assert "energy_trend" in trends
        assert "focus_trend" in trends
        assert "mood_trend" in trends
        assert trends["energy_trend"] == "declining"
        assert trends["focus_trend"] == "rising"

    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_empty_user(self, test_db):
        """Should return neutral defaults for user with no logs."""
        # Create test user
        user = User(
            email="test2@example.com",
            password_hash="hashed",
            display_name="Test User 2",
        )
        test_db.add(user)
        await test_db.flush()

        analyzer = PatternAnalyzer(test_db)
        trends = await analyzer.get_multi_metric_trends(str(user.id), days=7)

        assert trends["total_conversations"] == 0
        assert trends["mood_trend"] == "stable"
        assert trends["energy_trend"] == "stable"
        assert trends["focus_trend"] == "stable"

    @pytest.mark.asyncio
    async def test_get_multi_metric_trends_30d(self, test_db):
        """Should support 30-day window."""
        # Create test user
        user = User(
            email="test3@example.com",
            password_hash="hashed",
            display_name="Test User 3",
        )
        test_db.add(user)
        await test_db.flush()

        now = datetime.now(timezone.utc)
        for i in range(10):
            log = PatternLog(
                user_id=user.id,
                mood_score=0.2,
                energy_level=0.5,
                focus_score=0.5,
            )
            test_db.add(log)
            await test_db.flush()
            log.created_at = now - timedelta(days=25 - i)
            await test_db.flush()

        analyzer = PatternAnalyzer(test_db)
        trends = await analyzer.get_multi_metric_trends(str(user.id), days=30)
        assert trends["total_conversations"] == 10
