"""Trend analysis on pattern_logs for behavioral insights."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog


class PatternAnalyzer:
    """Analyzes pattern_logs for behavioral trends over time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_trends(
        self, user_id: str | UUID, days: int = 7
    ) -> dict[str, Any]:
        """Get aggregated mood/energy/focus trends for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(
            func.avg(PatternLog.mood_score).label("avg_mood"),
            func.avg(PatternLog.energy_level).label("avg_energy"),
            func.avg(PatternLog.focus_score).label("avg_focus"),
            func.count(PatternLog.id).label("total"),
            func.min(PatternLog.mood_score).label("min_mood"),
            func.max(PatternLog.mood_score).label("max_mood"),
        ).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= cutoff,
        )

        result = (await self.db.execute(stmt)).one()

        mood_trend = await self._calculate_trend(user_id, days, "mood_score")

        return {
            "avg_mood": round(float(result.avg_mood or 0), 2),
            "avg_energy": round(float(result.avg_energy or 0), 2),
            "avg_focus": round(float(result.avg_focus or 0), 2),
            "total_conversations": int(result.total or 0),
            "min_mood": round(float(result.min_mood or 0), 2),
            "max_mood": round(float(result.max_mood or 0), 2),
            "mood_trend": mood_trend,
        }

    async def _calculate_trend(
        self, user_id: str | UUID, days: int, column: str
    ) -> str:
        """Calculate if a metric is rising, declining, or stable."""
        now = datetime.now(timezone.utc)
        midpoint = now - timedelta(days=days / 2)
        cutoff = now - timedelta(days=days)

        col = getattr(PatternLog, column)

        stmt_first = select(func.avg(col)).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= cutoff,
            PatternLog.created_at < midpoint,
        )
        first_avg = (await self.db.execute(stmt_first)).scalar() or 0

        stmt_second = select(func.avg(col)).where(
            PatternLog.user_id == str(user_id),
            PatternLog.created_at >= midpoint,
        )
        second_avg = (await self.db.execute(stmt_second)).scalar() or 0

        diff = float(second_avg) - float(first_avg)
        if diff > 0.1:
            return "rising"
        elif diff < -0.1:
            return "declining"
        return "stable"

    async def get_last_analysis(self, user_id: str | UUID) -> datetime | None:
        """Get timestamp of the most recent analysis."""
        stmt = (
            select(PatternLog.created_at)
            .where(PatternLog.user_id == str(user_id))
            .order_by(PatternLog.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar()

    async def get_log_count(self, user_id: str | UUID) -> int:
        """Get total number of pattern logs for a user."""
        stmt = select(func.count(PatternLog.id)).where(
            PatternLog.user_id == str(user_id)
        )
        return (await self.db.execute(stmt)).scalar() or 0

    def format_for_prompt(self, trends: dict[str, Any]) -> str:
        """Format trends into a human-readable prompt section."""
        if trends["total_conversations"] == 0:
            return "Noch keine Verhaltensdaten vorhanden."

        mood_label = self._score_label(trends["avg_mood"], is_mood=True)
        energy_label = self._score_label(trends["avg_energy"])
        focus_label = self._score_label(trends["avg_focus"])
        trend_label = {
            "rising": "steigend",
            "declining": "fallend",
            "stable": "stabil",
        }.get(trends["mood_trend"], "unbekannt")

        return (
            f"Basierend auf {trends['total_conversations']} Gespraechen "
            f"der letzten Tage:\n"
            f"- Stimmung: {trends['avg_mood']} ({mood_label}, Trend: {trend_label})\n"
            f"- Energie: {trends['avg_energy']} ({energy_label})\n"
            f"- Fokus: {trends['avg_focus']} ({focus_label})"
        )

    @staticmethod
    def _score_label(score: float, is_mood: bool = False) -> str:
        if is_mood:
            if score >= 0.5:
                return "positiv"
            elif score >= 0.1:
                return "leicht positiv"
            elif score >= -0.1:
                return "neutral"
            elif score >= -0.5:
                return "leicht negativ"
            return "negativ"
        else:
            if score >= 0.7:
                return "hoch"
            elif score >= 0.4:
                return "mittel"
            return "niedrig"
