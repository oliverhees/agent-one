"""BrainDumpService for quick thought capture and task creation."""

import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


class BrainDumpService:
    """Parses free-text brain dumps into structured tasks."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process(self, user_id: str, text: str) -> dict[str, Any]:
        """Parse brain dump text and create tasks."""
        items = self._parse_text(text)
        created = []

        for item in items:
            task = Task(
                user_id=UUID(user_id),
                title=item[:200],  # Cap title length
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.OPEN,
            )
            self.db.add(task)
            created.append({"title": task.title, "priority": task.priority.value})

        await self.db.flush()

        return {
            "tasks_created": len(created),
            "tasks": created,
            "message": f"{len(created)} Aufgabe{'n' if len(created) != 1 else ''} aus deinem Brain Dump erstellt.",
        }

    @staticmethod
    def _parse_text(text: str) -> list[str]:
        """Parse free-text into individual task items."""
        # Remove numbered list prefixes (1. 2. 3. or - or *)
        text = re.sub(r"^\s*[\d]+[.)]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.MULTILINE)

        # Split by newlines first
        if "\n" in text:
            items = text.split("\n")
        # Then by " und " (German "and")
        elif " und " in text:
            items = text.split(" und ")
        # Then by commas
        elif "," in text:
            items = text.split(",")
        else:
            items = [text]

        # Clean up
        return [item.strip() for item in items if item.strip()]
