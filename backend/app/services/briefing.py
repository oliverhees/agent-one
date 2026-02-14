"""BriefingService for generating personalized Morning Briefings."""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.briefing import Briefing, BriefingStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.services.pattern_analyzer import PatternAnalyzer
from app.services.wellbeing import WellbeingService

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {
    "urgent": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

BRIEFING_SYSTEM_PROMPT = """Du bist Alice, ein einfuehlsamer ADHS-Coach. Erstelle ein kurzes, motivierendes Morning Briefing auf Deutsch.

Regeln:
- Maximal 150 Woerter
- Beginne mit einer persoenlichen Begruessung
- Erwaehne den Wellbeing-Score und den Trend
- Nenne die Top-Aufgaben (max 3) mit kurzer Begruendung
- Gib einen ADHS-spezifischen Tipp basierend auf den Trends
- Verwende einen warmen, ermutigenden Ton
- KEINE Emojis"""


class BriefingService:
    """Service for generating and managing Morning Briefings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pattern_analyzer = PatternAnalyzer(db)
        self.wellbeing_service = WellbeingService(db)

    async def generate_briefing(
        self, user_id: str, display_name: str | None = None, max_tasks: int = 3
    ) -> dict[str, Any]:
        """Generate a new Morning Briefing for today."""
        # 1. Get open tasks
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == UUID(user_id),
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        )
        all_tasks = result.scalars().all()

        # 2. Prioritize tasks
        prioritized = self._prioritize_tasks(all_tasks, max_tasks=max_tasks)

        # 3. Get wellbeing data
        wellbeing = await self.wellbeing_service.get_latest_score(user_id)
        if not wellbeing:
            wellbeing = {"score": 50, "zone": "yellow", "components": {}}

        # 4. Get recent trends
        trends = await self.pattern_analyzer.get_recent_trends(user_id, days=7)

        # 5. Build prompt context and generate LLM content
        context = self._build_prompt_context(
            display_name=display_name or "du",
            tasks=prioritized,
            wellbeing=wellbeing,
            trends=trends,
        )
        content = await self._generate_with_llm(context)

        # 6. Persist briefing
        briefing = Briefing(
            user_id=UUID(user_id),
            briefing_date=date.today(),
            content=content,
            tasks_suggested=prioritized,
            wellbeing_snapshot=wellbeing,
            status=BriefingStatus.GENERATED,
        )
        self.db.add(briefing)
        await self.db.flush()

        return {
            "id": str(briefing.id),
            "briefing_date": briefing.briefing_date,
            "content": content,
            "tasks_suggested": prioritized,
            "wellbeing_snapshot": wellbeing,
            "status": briefing.status,
            "read_at": None,
            "created_at": briefing.created_at,
        }

    async def get_today_briefing(self, user_id: str) -> dict[str, Any] | None:
        """Get today's briefing if it exists."""
        result = await self.db.execute(
            select(Briefing).where(
                Briefing.user_id == UUID(user_id),
                Briefing.briefing_date == date.today(),
            )
        )
        briefing = result.scalar_one_or_none()
        if not briefing:
            return None

        return {
            "id": str(briefing.id),
            "briefing_date": briefing.briefing_date,
            "content": briefing.content,
            "tasks_suggested": briefing.tasks_suggested,
            "wellbeing_snapshot": briefing.wellbeing_snapshot,
            "status": briefing.status,
            "read_at": briefing.read_at,
            "created_at": briefing.created_at,
        }

    async def get_briefing_history(self, user_id: str, days: int = 7) -> list[dict]:
        """Get briefing history for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(Briefing)
            .where(
                Briefing.user_id == UUID(user_id),
                Briefing.created_at >= cutoff,
            )
            .order_by(Briefing.briefing_date.desc())
        )
        briefings = result.scalars().all()
        return [
            {
                "id": str(b.id),
                "briefing_date": b.briefing_date,
                "content": b.content,
                "tasks_suggested": b.tasks_suggested,
                "wellbeing_snapshot": b.wellbeing_snapshot,
                "status": b.status,
                "read_at": b.read_at,
                "created_at": b.created_at,
            }
            for b in briefings
        ]

    async def mark_as_read(self, briefing_id: str, user_id: str) -> bool:
        """Mark a briefing as read."""
        result = await self.db.execute(
            select(Briefing).where(
                Briefing.id == UUID(briefing_id),
                Briefing.user_id == UUID(user_id),
            )
        )
        briefing = result.scalar_one_or_none()
        if not briefing:
            return False

        briefing.status = BriefingStatus.READ
        briefing.read_at = datetime.now(timezone.utc)
        return True

    @staticmethod
    def _prioritize_tasks(
        tasks: list, max_tasks: int = 3
    ) -> list[dict[str, Any]]:
        """Prioritize tasks by urgency and due date (ADHS-optimized: max N tasks)."""
        if not tasks:
            return []

        def sort_key(task):
            prio = PRIORITY_ORDER.get(task.priority.value, 2)
            # Boost tasks with soon due dates
            if task.due_date:
                hours_until = (task.due_date - datetime.now(timezone.utc)).total_seconds() / 3600
                if hours_until < 24:
                    prio -= 2
                elif hours_until < 72:
                    prio -= 1
            return prio

        sorted_tasks = sorted(tasks, key=sort_key)

        return [
            {
                "task_id": str(t.id),
                "title": t.title,
                "priority": t.priority.value,
                "reason": _reason_for_task(t),
            }
            for t in sorted_tasks[:max_tasks]
        ]

    @staticmethod
    def _build_prompt_context(
        display_name: str,
        tasks: list[dict],
        wellbeing: dict,
        trends: dict,
    ) -> str:
        """Build context string for the LLM prompt."""
        task_lines = ""
        for i, t in enumerate(tasks, 1):
            reason = f" — {t['reason']}" if t.get("reason") else ""
            task_lines += f"  {i}. {t['title']} (Prioritaet: {t['priority']}){reason}\n"

        if not task_lines:
            task_lines = "  Keine offenen Aufgaben.\n"

        mood_trend = trends.get("mood_trend", "stable")
        energy = trends.get("avg_energy", 0.5)
        score = wellbeing.get("score", 50)
        zone = wellbeing.get("zone", "yellow")

        return f"""Name: {display_name}
Wellbeing-Score: {score:.0f}/100 (Zone: {zone})
Stimmungstrend: {mood_trend}
Durchschnittliche Energie: {energy:.0%}
Heutige Aufgaben:
{task_lines}"""

    async def _generate_with_llm(self, context: str) -> str:
        """Generate briefing content using Claude API."""
        from app.core.config import settings

        api_key = settings.anthropic_api_key
        if not api_key:
            return self._generate_fallback(context)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 500,
                        "system": BRIEFING_SYSTEM_PROMPT,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Erstelle ein Morning Briefing mit diesem Kontext:\n\n{context}",
                            }
                        ],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
        except Exception:
            logger.exception("LLM briefing generation failed, using fallback")
            return self._generate_fallback(context)

    @staticmethod
    def _generate_fallback(context: str) -> str:
        """Generate a simple template-based briefing when LLM is unavailable."""
        lines = context.strip().split("\n")
        name = "du"
        score_line = ""
        for line in lines:
            if line.startswith("Name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("Wellbeing-Score:"):
                score_line = line.split(":", 1)[1].strip()

        return (
            f"Guten Morgen {name}!\n\n"
            f"Dein Wellbeing-Score: {score_line}\n\n"
            f"Konzentriere dich heute auf deine wichtigsten Aufgaben. "
            f"Mach Pausen wenn du sie brauchst und sei nicht zu streng mit dir."
        )


def _reason_for_task(task) -> str | None:
    """Generate a short reason why this task is prioritized."""
    if task.due_date:
        hours = (task.due_date - datetime.now(timezone.utc)).total_seconds() / 3600
        if hours < 0:
            return "Ueberfaellig"
        elif hours < 24:
            return "Faellig heute"
        elif hours < 72:
            return "Faellig in den naechsten Tagen"
    if task.priority.value == "urgent":
        return "Dringend"
    return None
