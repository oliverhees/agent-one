"""WellbeingService — computes aggregated wellbeing scores and manages interventions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention
from app.models.pattern_log import PatternLog
from app.models.user_stats import UserStats
from app.models.wellbeing_score import WellbeingScore
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

# Weights for score calculation (must sum to 1.0)
WEIGHTS = {
    "mood": 0.25,
    "energy": 0.20,
    "focus": 0.15,
    "task_completion": 0.15,
    "streak": 0.10,
    "consistency": 0.15,
}


class WellbeingService:
    """Computes and stores wellbeing scores, manages interventions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)

    async def calculate_and_store(self, user_id: str) -> dict[str, Any]:
        """Calculate wellbeing score from recent data and persist it."""
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)
        stats = await self._get_user_stats(user_id)
        score, components = self._compute_score(trends, stats)
        zone = self._zone_for_score(score)

        wellbeing = WellbeingScore(
            user_id=user_id,
            score=round(score, 1),
            zone=zone,
            components=components,
        )
        self.db.add(wellbeing)
        await self.db.flush()

        logger.info("Wellbeing score for user %s: %.1f (%s)", user_id, score, zone)

        return {
            "score": round(score, 1),
            "zone": zone,
            "components": components,
            "calculated_at": wellbeing.created_at,
        }

    def _compute_score(
        self, trends: dict[str, Any], stats: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """Compute weighted wellbeing score from trends and stats."""
        total_convos = trends.get("total_conversations", 0)

        raw_mood = trends.get("avg_mood", 0)
        mood_norm = (raw_mood + 1) / 2

        energy_norm = trends.get("avg_energy", 0)
        focus_norm = trends.get("avg_focus", 0)

        tasks_done = stats.get("tasks_completed", 0)
        task_norm = min(tasks_done / 20, 1.0) if tasks_done else 0

        streak = stats.get("current_streak", 0)
        streak_norm = min(streak / 14, 1.0)

        consistency_norm = min(total_convos / 14, 1.0) if total_convos else 0

        if total_convos == 0 and tasks_done == 0 and streak == 0:
            return 50.0, {
                "mood": 0.5, "energy": 0.5, "focus": 0.5,
                "task_completion": 0, "streak": 0, "consistency": 0,
                "note": "Noch keine Daten vorhanden",
            }

        weighted = (
            mood_norm * WEIGHTS["mood"]
            + energy_norm * WEIGHTS["energy"]
            + focus_norm * WEIGHTS["focus"]
            + task_norm * WEIGHTS["task_completion"]
            + streak_norm * WEIGHTS["streak"]
            + consistency_norm * WEIGHTS["consistency"]
        )

        score = round(weighted * 100, 1)
        score = max(0, min(100, score))

        components = {
            "mood": round(mood_norm, 3),
            "energy": round(energy_norm, 3),
            "focus": round(focus_norm, 3),
            "task_completion": round(task_norm, 3),
            "streak": round(streak_norm, 3),
            "consistency": round(consistency_norm, 3),
        }

        return score, components

    @staticmethod
    def _zone_for_score(score: float) -> str:
        if score <= 30:
            return "red"
        elif score <= 60:
            return "yellow"
        return "green"

    async def get_latest_score(self, user_id: str) -> dict[str, Any] | None:
        stmt = (
            select(WellbeingScore)
            .where(WellbeingScore.user_id == user_id)
            .order_by(WellbeingScore.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        ws = result.scalar_one_or_none()
        if not ws:
            return None
        return {
            "score": ws.score,
            "zone": ws.zone,
            "components": ws.components,
            "calculated_at": ws.created_at,
        }

    async def get_score_history(self, user_id: str, days: int = 7) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(WellbeingScore)
            .where(WellbeingScore.user_id == user_id, WellbeingScore.created_at >= cutoff)
            .order_by(WellbeingScore.created_at.asc())
        )
        result = await self.db.execute(stmt)
        scores = result.scalars().all()

        score_list = [
            {"score": s.score, "zone": s.zone, "components": s.components, "calculated_at": s.created_at}
            for s in scores
        ]

        avg = sum(s.score for s in scores) / len(scores) if scores else 50.0

        trend = "stable"
        if len(scores) >= 2:
            mid = len(scores) // 2
            first_half_avg = sum(s.score for s in scores[:mid]) / mid
            second_half_avg = sum(s.score for s in scores[mid:]) / (len(scores) - mid)
            diff = second_half_avg - first_half_avg
            if diff > 3:
                trend = "rising"
            elif diff < -3:
                trend = "declining"

        return {"scores": score_list, "trend": trend, "average_score": round(avg, 1), "days": days}

    async def get_active_interventions(self, user_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(Intervention)
            .where(Intervention.user_id == user_id, Intervention.status == "pending")
            .order_by(Intervention.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        interventions = result.scalars().all()
        return [
            {"id": i.id, "type": i.type, "trigger_pattern": i.trigger_pattern,
             "message": i.message, "status": i.status, "created_at": i.created_at}
            for i in interventions
        ]

    async def update_intervention_status(self, intervention_id: str, user_id: str, new_status: str) -> bool:
        stmt = (
            update(Intervention)
            .where(Intervention.id == intervention_id, Intervention.user_id == user_id)
            .values(status=new_status)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        stmt = select(UserStats).where(UserStats.user_id == user_id)
        result = await self.db.execute(stmt)
        stats = result.scalar_one_or_none()
        if not stats:
            return {"tasks_completed": 0, "current_streak": 0}
        return {"tasks_completed": stats.tasks_completed, "current_streak": stats.current_streak}
