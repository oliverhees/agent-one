"""MemoryService – Orchestrator for Graphiti, NLPAnalyzer and PatternAnalyzer.

Central coordinator for ALICE's memory system:
- Called AFTER conversations (process_episode) to analyze and store
- Called BEFORE chats (get_context) to retrieve relevant memory
- Provides DSGVO endpoints (get_status, export_user_data, delete_user_data)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_log import PatternLog
from app.schemas.memory import ConversationAnalysis, PatternLogResponse
from app.services.graphiti_client import GraphitiClient
from app.services.nlp_analyzer import NLPAnalyzer
from app.services.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)


class MemoryService:
    """Orchestrates knowledge graph, NLP analysis and trend detection.

    Usage::

        service = MemoryService(db, graphiti_client)

        # After a conversation ends
        await service.process_episode(user_id, conversation_id, messages)

        # Before a new chat turn
        context = await service.get_context(user_id, query)
        prompt_section = service.format_context_for_prompt(context)
    """

    def __init__(self, db: AsyncSession, graphiti: GraphitiClient) -> None:
        self.db = db
        self.graphiti = graphiti
        self.nlp_analyzer = NLPAnalyzer()
        self.pattern_analyzer = PatternAnalyzer(db)

    # ------------------------------------------------------------------
    # Process Episode (post-conversation)
    # ------------------------------------------------------------------

    async def process_episode(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
    ) -> None:
        """Analyze a completed conversation and store results.

        Called asynchronously after a conversation ends.  Adds the
        conversation to the knowledge graph, runs NLP analysis, and
        persists a :class:`PatternLog` for trend tracking.

        Args:
            user_id: The user's UUID string.
            conversation_id: The conversation's UUID string.
            messages: List of message dicts with ``role`` and ``content`` keys.
        """
        if not messages:
            logger.debug("process_episode: no messages, skipping (user=%s)", user_id)
            return

        # 1. Format messages into conversation text
        conversation_text = self._format_messages(messages)

        # 2. Add episode to Graphiti knowledge graph
        episode_id: str | None = None
        try:
            episode_id = await self.graphiti.add_episode(
                name=f"conversation:{conversation_id}",
                content=conversation_text,
                user_id=user_id,
            )
            if episode_id:
                logger.info(
                    "Added episode %s for user %s (conversation %s)",
                    episode_id, user_id, conversation_id,
                )
            else:
                logger.debug(
                    "Graphiti returned None for episode (disabled or error), user=%s",
                    user_id,
                )
        except Exception:
            logger.exception("Failed to add episode to Graphiti for user %s", user_id)

        # 3. Run NLP analysis
        analysis: ConversationAnalysis
        try:
            analysis = await self.nlp_analyzer.analyze(messages)
            logger.debug(
                "NLP analysis for user %s: mood=%.2f energy=%.2f focus=%.2f patterns=%s",
                user_id, analysis.mood_score, analysis.energy_level,
                analysis.focus_score, analysis.detected_patterns,
            )
        except Exception:
            logger.exception("NLP analysis failed for user %s", user_id)
            return

        # 4. Store PatternLog in DB
        try:
            pattern_log = PatternLog(
                user_id=user_id,
                conversation_id=conversation_id,
                episode_id=episode_id,
                mood_score=analysis.mood_score,
                energy_level=analysis.energy_level,
                focus_score=analysis.focus_score,
            )
            self.db.add(pattern_log)
            await self.db.flush()
            logger.info(
                "Stored PatternLog for user %s (conversation %s)",
                user_id, conversation_id,
            )
        except Exception:
            logger.exception("Failed to store PatternLog for user %s", user_id)

    # ------------------------------------------------------------------
    # Get Context (pre-chat)
    # ------------------------------------------------------------------

    async def get_context(
        self,
        user_id: str,
        query: str,
    ) -> dict[str, Any]:
        """Retrieve relevant memory context for an upcoming chat turn.

        Args:
            user_id: The user's UUID string.
            query: The user's current message / search query.

        Returns:
            Dict with ``facts`` (list of fact dicts from Graphiti) and
            ``trends`` (aggregated mood/energy/focus from PatternAnalyzer).
        """
        # 1. Search knowledge graph for relevant facts
        facts: list[dict[str, Any]] = []
        try:
            facts = await self.graphiti.search(
                query=query,
                user_id=user_id,
                num_results=10,
            )
        except Exception:
            logger.exception("Graphiti search failed for user %s", user_id)

        # 2. Get recent behavioral trends
        trends: dict[str, Any] = {"total_conversations": 0}
        try:
            trends = await self.pattern_analyzer.get_recent_trends(user_id)
        except Exception:
            logger.exception("Pattern trend retrieval failed for user %s", user_id)

        return {
            "facts": facts,
            "trends": trends,
        }

    # ------------------------------------------------------------------
    # Format Context for Prompt
    # ------------------------------------------------------------------

    def format_context_for_prompt(self, context: dict[str, Any]) -> str:
        """Format retrieved context into a system prompt section.

        Args:
            context: Dict returned by :meth:`get_context`.

        Returns:
            A multi-line string to inject into the system prompt, or
            an empty string if there is no context.
        """
        facts = context.get("facts", [])
        trends = context.get("trends", {})

        has_facts = bool(facts)
        has_trends = trends.get("total_conversations", 0) > 0

        if not has_facts and not has_trends:
            return ""

        sections: list[str] = []

        # Facts section
        if has_facts:
            lines = ["## Was du ueber den User weisst:"]
            for fact in facts:
                fact_text = fact.get("fact", "")
                if fact_text:
                    lines.append(f"- {fact_text}")
            sections.append("\n".join(lines))

        # Trends section
        if has_trends:
            trend_text = self.pattern_analyzer.format_for_prompt(trends)
            sections.append(f"## Aktuelle Verhaltenstrends:\n{trend_text}")

            # Recommendations section
            recommendations = self._build_recommendations(trends)
            if recommendations:
                rec_lines = ["## Handlungsempfehlung:"]
                for rec in recommendations:
                    rec_lines.append(f"- {rec}")
                sections.append("\n".join(rec_lines))

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Recommendations Builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_recommendations(trends: dict[str, Any]) -> list[str]:
        """Build actionable recommendations based on behavioral trends.

        Args:
            trends: Trends dict from :meth:`PatternAnalyzer.get_recent_trends`.

        Returns:
            A list of recommendation strings (may be empty).
        """
        recommendations: list[str] = []

        avg_focus = trends.get("avg_focus", 0.5)
        avg_mood = trends.get("avg_mood", 0.0)
        mood_trend = trends.get("mood_trend", "stable")

        if avg_focus < 0.3:
            recommendations.append(
                "Fokus ist niedrig — schlage konkrete Fokus-Techniken vor "
                "(z.B. Pomodoro, Body Doubling, Musik)."
            )

        if avg_mood < -0.2:
            recommendations.append(
                "Stimmung ist niedrig — sei besonders empathisch und validierend. "
                "Vermeide Druck und betone kleine Erfolge."
            )

        if mood_trend == "declining":
            recommendations.append(
                "Stimmungstrend ist fallend — erwaehne dies vorsichtig und "
                "frage behutsam nach moeglichen Ursachen."
            )

        return recommendations

    # ------------------------------------------------------------------
    # DSGVO / Status Endpoints
    # ------------------------------------------------------------------

    async def get_status(self, user_id: str) -> dict[str, Any]:
        """Return the memory system status for a user.

        Returns:
            Dict with ``enabled``, ``total_episodes``,
            ``total_entities`` and ``last_analysis_at``.
        """
        total_entities = 0
        try:
            total_entities = await self.graphiti.get_entity_count(user_id)
        except Exception:
            logger.exception("Failed to get entity count for user %s", user_id)

        total_episodes = 0
        last_analysis_at: datetime | None = None
        try:
            total_episodes = await self.pattern_analyzer.get_log_count(user_id)
            last_analysis_at = await self.pattern_analyzer.get_last_analysis(user_id)
        except Exception:
            logger.exception("Failed to get pattern log stats for user %s", user_id)

        return {
            "enabled": self.graphiti.enabled,
            "total_episodes": total_episodes,
            "total_entities": total_entities,
            "last_analysis_at": last_analysis_at,
        }

    async def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Export all stored data for a user (DSGVO Art. 15).

        Returns:
            Dict with ``entities``, ``relations``, ``pattern_logs``
            and ``exported_at``.
        """
        # 1. Get entities from knowledge graph
        entities: list[dict[str, Any]] = []
        try:
            entities = await self.graphiti.search(
                query="*",
                user_id=user_id,
                num_results=1000,
            )
        except Exception:
            logger.exception("Failed to export graph data for user %s", user_id)

        # 2. Get all pattern logs from DB
        pattern_logs: list[PatternLogResponse] = []
        try:
            stmt = (
                select(PatternLog)
                .where(PatternLog.user_id == str(user_id))
                .order_by(PatternLog.created_at.desc())
            )
            result = await self.db.execute(stmt)
            logs = result.scalars().all()
            pattern_logs = [PatternLogResponse.model_validate(log) for log in logs]
        except Exception:
            logger.exception("Failed to export pattern logs for user %s", user_id)

        return {
            "entities": entities,
            "relations": [],  # Graphiti search returns edges as facts
            "pattern_logs": pattern_logs,
            "exported_at": datetime.now(timezone.utc),
        }

    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all stored data for a user (DSGVO Art. 17).

        Removes both knowledge graph data and pattern logs.

        Returns:
            ``True`` if all deletions succeeded, ``False`` if any failed.
        """
        success = True

        # 1. Delete knowledge graph data
        try:
            graph_deleted = await self.graphiti.delete_user_data(user_id)
            if not graph_deleted:
                logger.error("Failed to delete graph data for user %s", user_id)
                success = False
        except Exception:
            logger.exception("Error deleting graph data for user %s", user_id)
            success = False

        # 2. Delete pattern logs from DB
        try:
            stmt = (
                select(PatternLog)
                .where(PatternLog.user_id == str(user_id))
            )
            result = await self.db.execute(stmt)
            logs = result.scalars().all()
            for log in logs:
                await self.db.delete(log)
            await self.db.flush()
            logger.info("Deleted %d pattern logs for user %s", len(logs), user_id)
        except Exception:
            logger.exception("Error deleting pattern logs for user %s", user_id)
            success = False

        return success

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_messages(messages: list[dict[str, str]]) -> str:
        """Format message dicts into a readable conversation text."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"ALICE: {content}")
            else:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)
