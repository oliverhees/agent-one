"""InterventionEngine — detects 7 ADHS-specific patterns and creates interventions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention
from app.models.pattern_log import PatternLog
from app.models.task import Task, TaskStatus
from app.models.user_stats import UserStats
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

INTERVENTION_COOLDOWN_HOURS = 12

MESSAGES = {
    "hyperfocus": "Du bist deep drin — denk an eine Pause! Steh kurz auf, trink Wasser.",
    "procrastination": "Lass uns die Aufgabe kleiner machen. Was waere der kleinste erste Schritt?",
    "decision_fatigue": "Zu viele Optionen? Fokus auf DIESE eine Sache. Den Rest ignorieren wir.",
    "transition": "Gleich steht ein Wechsel an — nimm dir 2 Minuten Pause dazwischen.",
    "energy_crash": "Deine Energie sinkt seit Tagen. Heute leichtere Aufgaben — und frueher Schluss.",
    "sleep_disruption": "Spaete Nutzung + wenig Energie morgens? Quiet-Hours koennten helfen.",
    "social_masking": "Hohe Produktivitaet aber sinkende Stimmung? Goenn dir etwas fuer DICH.",
}


class InterventionEngine:
    """Detects ADHS-specific behavioral patterns and creates proactive interventions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)

    async def evaluate(self, user_id: str) -> list[dict[str, Any]]:
        """Evaluate user patterns and create interventions for detected issues.

        Returns a list of newly created intervention dicts.
        """
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)
        stats = await self._get_user_stats(user_id)
        recent_logs = await self._get_recent_logs(user_id, days=3)

        if trends.get("total_conversations", 0) == 0:
            return []

        detected = self._detect_patterns(trends, stats, recent_logs)

        created: list[dict[str, Any]] = []
        for pattern in detected:
            if await self._has_recent_intervention(user_id, pattern["type"]):
                continue

            intervention = Intervention(
                user_id=user_id,
                type=pattern["type"],
                trigger_pattern=pattern["trigger"],
                message=pattern["message"],
                status="pending",
            )
            self.db.add(intervention)
            await self.db.flush()

            created.append({
                "id": intervention.id,
                "type": intervention.type,
                "trigger_pattern": intervention.trigger_pattern,
                "message": intervention.message,
                "status": "pending",
                "created_at": intervention.created_at,
            })

        if created:
            logger.info(
                "Created %d interventions for user %s: %s",
                len(created),
                user_id,
                [c["type"] for c in created],
            )

        return created

    def _detect_patterns(
        self,
        trends: dict[str, Any],
        stats: dict[str, Any],
        recent_logs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect ADHS-specific behavioral patterns from trends, stats, and logs.

        Checks for 7 patterns:
        1. Hyperfocus — sustained high focus
        2. Procrastination Spiral — low energy + low mood + few tasks done
        3. Decision Fatigue — many open tasks + low focus
        4. Energy Crash — consecutively declining energy
        5. Social Masking — high productivity + declining mood
        6. Sleep Disruption — very low energy + negative mood
        7. Transition — placeholder for future real-time context switch detection
        """
        detected: list[dict[str, Any]] = []
        avg_focus = trends.get("avg_focus", 0.5)
        avg_energy = trends.get("avg_energy", 0.5)
        avg_mood = trends.get("avg_mood", 0.0)
        mood_trend = trends.get("mood_trend", "stable")
        tasks_completed = stats.get("tasks_completed", 0)
        open_tasks = stats.get("open_tasks", 0)
        streak = stats.get("current_streak", 0)  # noqa: F841 — reserved for future use

        # 1. Hyperfocus: Focus > 0.9
        if avg_focus > 0.9:
            detected.append({
                "type": "hyperfocus",
                "trigger": f"Focus {avg_focus:.2f} > 0.9",
                "message": MESSAGES["hyperfocus"],
            })

        # 2. Procrastination Spiral: low task completion + declining energy + low mood
        if avg_energy < 0.3 and avg_mood < -0.1 and tasks_completed < 3:
            detected.append({
                "type": "procrastination",
                "trigger": f"Energy {avg_energy:.2f}, mood {avg_mood:.2f}, tasks {tasks_completed}",
                "message": MESSAGES["procrastination"],
            })

        # 3. Decision Fatigue: many open tasks + low focus
        if open_tasks >= 5 and avg_focus < 0.3:
            detected.append({
                "type": "decision_fatigue",
                "trigger": f"{open_tasks} open tasks, focus {avg_focus:.2f}",
                "message": MESSAGES["decision_fatigue"],
            })

        # 4. Energy Crash: energy declining for 3+ consecutive entries
        if len(recent_logs) >= 3:
            energy_vals = [log.get("energy_level", 0.5) for log in recent_logs[-3:]]
            if all(energy_vals[i] > energy_vals[i + 1] for i in range(len(energy_vals) - 1)):
                if avg_energy < 0.3:
                    detected.append({
                        "type": "energy_crash",
                        "trigger": f"Energy declining: {[round(e, 2) for e in energy_vals]}",
                        "message": MESSAGES["energy_crash"],
                    })

        # 5. Social Masking: high productivity + declining mood
        if tasks_completed >= 10 and avg_mood < -0.2 and mood_trend == "declining":
            detected.append({
                "type": "social_masking",
                "trigger": f"Tasks {tasks_completed}, mood {avg_mood:.2f} ({mood_trend})",
                "message": MESSAGES["social_masking"],
            })

        # 6. Sleep Disruption: low energy + negative mood (simplified proxy)
        if avg_energy < 0.25 and avg_mood < 0:
            if not any(p["type"] == "energy_crash" for p in detected):
                detected.append({
                    "type": "sleep_disruption",
                    "trigger": f"Low energy {avg_energy:.2f} + negative mood {avg_mood:.2f}",
                    "message": MESSAGES["sleep_disruption"],
                })

        # 7. Transition: context switch needed — placeholder for future real-time detection

        return detected

    async def _has_recent_intervention(self, user_id: str, intervention_type: str) -> bool:
        """Check if an intervention of this type was already created within the cooldown window."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=INTERVENTION_COOLDOWN_HOURS)
        stmt = (
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.user_id == user_id,
                Intervention.type == intervention_type,
                Intervention.created_at >= cutoff,
            )
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def _get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Fetch user gamification stats and count of open tasks."""
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
        """Fetch recent pattern logs ordered chronologically."""
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
        logs = result.scalars().all()
        return [
            {
                "mood_score": log.mood_score,
                "energy_level": log.energy_level,
                "focus_score": log.focus_score,
            }
            for log in logs
        ]
