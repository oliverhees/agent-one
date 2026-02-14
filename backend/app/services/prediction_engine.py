"""PredictionEngine — predicts ADHS behavioral patterns before they happen."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.pattern_log import PatternLog
from app.models.task import Task, TaskStatus
from app.models.user_stats import UserStats
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

PREDICTION_COOLDOWN_HOURS = 24
CONFIDENCE_THRESHOLD = 0.6


class PredictionEngine:
    """Predicts ADHS behavioral patterns using rule-based analysis with optional Graphiti enrichment."""

    def __init__(self, db: AsyncSession, graphiti_client: Any = None) -> None:
        self.db = db
        self.analyzer = PatternAnalyzer(db)
        self.graphiti = graphiti_client

    async def predict(self, user_id: str) -> list[dict[str, Any]]:
        """Run all prediction rules and store results."""
        trends_7d = await self.analyzer.get_multi_metric_trends(user_id, days=7)
        trends_30d = await self.analyzer.get_multi_metric_trends(user_id, days=30)

        if trends_7d["total_conversations"] == 0:
            return []

        stats = await self._get_user_stats(user_id)
        recent_logs = await self._get_recent_logs(user_id, days=3)

        candidates: list[dict[str, Any]] = []

        for rule in [
            self._predict_energy_crash,
            self._predict_procrastination,
            self._predict_hyperfocus,
            self._predict_decision_fatigue,
            self._predict_sleep_disruption,
            self._predict_social_masking,
        ]:
            result = rule(trends_7d, trends_30d, stats, recent_logs)
            if result and result["confidence"] >= CONFIDENCE_THRESHOLD:
                candidates.append(result)

        created: list[dict[str, Any]] = []
        for candidate in candidates:
            if await self._has_recent_prediction(user_id, candidate["pattern_type"]):
                continue

            if self.graphiti and getattr(self.graphiti, "enabled", False):
                candidate["graphiti_context"] = await self._enrich_with_graphiti(
                    user_id, candidate["pattern_type"]
                )
            else:
                candidate["graphiti_context"] = {}

            prediction = PredictedPattern(
                user_id=user_id,
                pattern_type=candidate["pattern_type"],
                confidence=candidate["confidence"],
                predicted_for=candidate["predicted_for"],
                time_horizon=candidate["time_horizon"],
                trigger_factors=candidate["trigger_factors"],
                graphiti_context=candidate["graphiti_context"],
                status=PredictionStatus.ACTIVE,
            )
            self.db.add(prediction)
            await self.db.flush()

            created.append({
                "id": str(prediction.id),
                "pattern_type": prediction.pattern_type,
                "confidence": prediction.confidence,
                "predicted_for": prediction.predicted_for.isoformat(),
                "time_horizon": prediction.time_horizon,
                "trigger_factors": prediction.trigger_factors,
                "graphiti_context": prediction.graphiti_context,
                "status": prediction.status,
            })

        if created:
            await self.db.commit()
            logger.info(
                "Created %d predictions for user %s: %s",
                len(created), user_id, [c["pattern_type"] for c in created],
            )

        return created

    async def expire_old_predictions(self, user_id: str) -> int:
        """Expire active predictions whose predicted_for is in the past."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(PredictedPattern)
            .where(
                PredictedPattern.user_id == user_id,
                PredictedPattern.status == PredictionStatus.ACTIVE,
                PredictedPattern.predicted_for < now,
            )
        )
        result = await self.db.execute(stmt)
        expired = result.scalars().all()

        for p in expired:
            p.status = PredictionStatus.EXPIRED
            p.resolved_at = now

        await self.db.commit()
        return len(expired)

    # ------------------------------------------------------------------
    # Prediction Rules
    # ------------------------------------------------------------------

    def _predict_energy_crash(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["energy_trend"] == "declining":
            confidence += 0.35
            factors["energy_trend_7d"] = "declining"
        if t7["avg_energy"] < 0.4:
            confidence += 0.25
            factors["avg_energy_7d"] = t7["avg_energy"]
        if t7["focus_trend"] == "declining":
            confidence += 0.15
            factors["focus_trend_7d"] = "declining"
        if t30["avg_energy"] > t7["avg_energy"] + 0.15:
            confidence += 0.25
            factors["energy_drop_vs_30d"] = round(t30["avg_energy"] - t7["avg_energy"], 2)

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "energy_crash",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_procrastination(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_energy"] < 0.35:
            confidence += 0.25
            factors["low_energy"] = t7["avg_energy"]
        if t7["avg_mood"] < -0.1:
            confidence += 0.2
            factors["negative_mood"] = t7["avg_mood"]
        if stats.get("tasks_completed", 0) < 3:
            confidence += 0.2
            factors["low_task_completion"] = stats.get("tasks_completed", 0)
        if t7["mood_trend"] == "declining":
            confidence += 0.2
            factors["mood_declining"] = True
        if t30["avg_energy"] > t7["avg_energy"] + 0.1:
            confidence += 0.15
            factors["energy_below_baseline"] = True

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "procrastination",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=3),
            "time_horizon": "3d",
            "trigger_factors": factors,
        }

    def _predict_hyperfocus(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_focus"] > 0.85:
            confidence += 0.35
            factors["high_focus"] = t7["avg_focus"]
        if t7["focus_trend"] == "rising":
            confidence += 0.25
            factors["focus_rising"] = True
        if t7["avg_energy"] < 0.4:
            confidence += 0.2
            factors["energy_depleting"] = t7["avg_energy"]
        if t7["avg_focus"] > t30["avg_focus"] + 0.15:
            confidence += 0.2
            factors["focus_above_baseline"] = round(t7["avg_focus"] - t30["avg_focus"], 2)

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "hyperfocus",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_decision_fatigue(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        open_tasks = stats.get("open_tasks", 0)
        if open_tasks >= 5:
            confidence += 0.3
            factors["many_open_tasks"] = open_tasks
        if t7["avg_focus"] < 0.35:
            confidence += 0.25
            factors["low_focus"] = t7["avg_focus"]
        if t7["focus_trend"] == "declining":
            confidence += 0.2
            factors["focus_declining"] = True
        if open_tasks >= 8:
            confidence += 0.15
            factors["task_overload"] = open_tasks
        if t7["avg_mood"] < 0:
            confidence += 0.1
            factors["negative_mood"] = t7["avg_mood"]

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "decision_fatigue",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": factors,
        }

    def _predict_sleep_disruption(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        if t7["avg_energy"] < 0.3:
            confidence += 0.3
            factors["very_low_energy"] = t7["avg_energy"]
        if t7["avg_mood"] < -0.1:
            confidence += 0.2
            factors["negative_mood"] = t7["avg_mood"]
        if t7["energy_trend"] == "declining":
            confidence += 0.2
            factors["energy_declining"] = True
        if t30["avg_energy"] > t7["avg_energy"] + 0.2:
            confidence += 0.2
            factors["significant_energy_drop"] = round(t30["avg_energy"] - t7["avg_energy"], 2)
        if t7["avg_focus"] < 0.3:
            confidence += 0.1
            factors["low_focus_too"] = t7["avg_focus"]

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "sleep_disruption",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=3),
            "time_horizon": "3d",
            "trigger_factors": factors,
        }

    def _predict_social_masking(
        self, t7: dict, t30: dict, stats: dict, logs: list
    ) -> dict[str, Any] | None:
        confidence = 0.0
        factors = {}

        tasks_completed = stats.get("tasks_completed", 0)
        if tasks_completed >= 8:
            confidence += 0.3
            factors["high_productivity"] = tasks_completed
        if t7["avg_mood"] < -0.1:
            confidence += 0.25
            factors["declining_mood"] = t7["avg_mood"]
        if t7["mood_trend"] == "declining":
            confidence += 0.25
            factors["mood_trend_declining"] = True
        if t7["avg_focus"] > 0.7:
            confidence += 0.1
            factors["high_focus_masking"] = t7["avg_focus"]
        if t30["avg_mood"] > t7["avg_mood"] + 0.15:
            confidence += 0.1
            factors["mood_below_baseline"] = True

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        return {
            "pattern_type": "social_masking",
            "confidence": min(confidence, 1.0),
            "predicted_for": datetime.now(timezone.utc) + timedelta(days=7),
            "time_horizon": "7d",
            "trigger_factors": factors,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _enrich_with_graphiti(self, user_id: str, pattern_type: str) -> dict[str, Any]:
        """Query Graphiti for contextual facts related to a pattern type."""
        try:
            facts = await self.graphiti.search(
                query=f"ADHS {pattern_type} Verhaltensmuster",
                user_id=user_id,
                num_results=5,
            )
            return {
                "related_facts": facts,
                "enrichment_time": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.warning("Graphiti enrichment failed for %s: %s", pattern_type, exc)
            return {}

    async def _has_recent_prediction(self, user_id: str, pattern_type: str) -> bool:
        """Check if an active prediction of this type exists within cooldown."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=PREDICTION_COOLDOWN_HOURS)
        stmt = (
            select(func.count())
            .select_from(PredictedPattern)
            .where(
                PredictedPattern.user_id == user_id,
                PredictedPattern.pattern_type == pattern_type,
                PredictedPattern.status == PredictionStatus.ACTIVE,
                PredictedPattern.created_at >= cutoff,
            )
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        stats_result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        stats = stats_result.scalar_one_or_none()

        open_count_result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        )
        open_tasks = open_count_result.scalar() or 0

        if not stats:
            return {"tasks_completed": 0, "current_streak": 0, "open_tasks": open_tasks}

        return {
            "tasks_completed": stats.tasks_completed,
            "current_streak": stats.current_streak,
            "open_tasks": open_tasks,
        }

    async def _get_recent_logs(self, user_id: str, days: int = 3) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(PatternLog)
            .where(
                PatternLog.user_id == user_id,
                PatternLog.created_at >= cutoff,
            )
            .order_by(PatternLog.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return [
            {
                "mood_score": log.mood_score,
                "energy_level": log.energy_level,
                "focus_score": log.focus_score,
            }
            for log in result.scalars().all()
        ]
