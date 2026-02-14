"""ContextBuilder – enriches system prompts with memory context."""

from __future__ import annotations

import logging

from app.services.memory import MemoryService

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Enriches the system prompt with knowledge graph context and trends.

    Called synchronously before each chat response. Designed for low
    latency (~300ms) with graceful degradation on failure.
    """

    def __init__(self, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    async def enrich(
        self,
        base_prompt: str,
        user_id: str,
        user_message: str,
    ) -> str:
        """Enrich the system prompt with relevant memory context.

        Returns the base prompt unmodified if memory is unavailable.
        """
        try:
            context = await self.memory_service.get_context(
                user_id=user_id,
                query=user_message,
            )

            memory_block = self.memory_service.format_context_for_prompt(context)

            if not memory_block:
                return base_prompt

            return f"{base_prompt}\n\n{memory_block}"

        except Exception:
            logger.exception("Failed to enrich system prompt with memory")
            return base_prompt
