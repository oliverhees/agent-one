"""Task breakdown service for AI-powered task decomposition."""

import json
import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AIServiceUnavailableError,
    TaskNotFoundError,
    TaskAlreadyHasSubtasksError,
)
from app.models.task import Task, TaskSource, TaskStatus
from app.schemas.task import TaskResponse
from app.schemas.task_breakdown import (
    BreakdownParentTask,
    BreakdownResponse,
    BreakdownSuggestedSubtask,
    BreakdownConfirmSubtask,
    BreakdownConfirmParent,
    BreakdownConfirmResponse,
)
from app.services.ai import AIService

logger = logging.getLogger(__name__)


class TaskBreakdownService:
    """Service for AI-powered task breakdown."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def _get_task_with_checks(self, task_id: UUID, user_id: UUID) -> Task:
        """Get task with ownership and subtask checks."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise TaskNotFoundError(task_id=str(task_id))

        # Check if task already has subtasks
        subtask_count_result = await self.db.execute(
            select(func.count()).select_from(Task).where(Task.parent_id == task_id)
        )
        subtask_count = subtask_count_result.scalar_one()
        if subtask_count > 0:
            raise TaskAlreadyHasSubtasksError(task_id=str(task_id))

        return task

    async def generate_breakdown(self, task_id: UUID, user_id: UUID) -> BreakdownResponse:
        """Generate AI-powered sub-task suggestions for a task."""
        task = await self._get_task_with_checks(task_id, user_id)

        description_part = f"\n{task.description}" if task.description else ""
        prompt = (
            f"Zerlege folgende Aufgabe in 3-7 kleine, konkrete Schritte "
            f"(max 30 Min pro Schritt): {task.title}{description_part}\n\n"
            f"Antworte NUR mit einem JSON-Array. Kein weiterer Text. Format:\n"
            f'[{{"title": "...", "description": "...", "estimated_minutes": 15}}]'
        )

        try:
            # Collect the full response from stream
            full_response = ""
            async for chunk in self.ai_service.stream_response(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=(
                    "Du bist ALICE, ein ADHS-Coach. Du zerlegst grosse Aufgaben in "
                    "kleine, machbare Schritte. Antworte NUR mit validem JSON."
                ),
            ):
                full_response += chunk

            # Parse the JSON response
            subtasks = self._parse_breakdown_response(full_response)

        except AIServiceUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Task breakdown failed: {e}")
            raise AIServiceUnavailableError(
                detail=f"Task breakdown generation failed: {str(e)}"
            )

        return BreakdownResponse(
            parent_task=BreakdownParentTask(
                id=task.id,
                title=task.title,
                priority=task.priority.value,
                estimated_minutes=task.estimated_minutes,
            ),
            suggested_subtasks=subtasks,
        )

    @staticmethod
    def _parse_breakdown_response(response: str) -> list[BreakdownSuggestedSubtask]:
        """Parse the LLM response into structured sub-task suggestions."""
        # Try to extract JSON array from response
        response = response.strip()

        # Find JSON array in response (might be wrapped in markdown code blocks)
        json_start = response.find("[")
        json_end = response.rfind("]")
        if json_start == -1 or json_end == -1:
            raise ValueError("No JSON array found in AI response")

        json_str = response[json_start:json_end + 1]
        items = json.loads(json_str)

        if not isinstance(items, list) or len(items) < 1:
            raise ValueError("AI response must contain at least 1 sub-task")

        subtasks = []
        for i, item in enumerate(items[:7], start=1):  # Max 7 subtasks
            subtasks.append(BreakdownSuggestedSubtask(
                title=str(item.get("title", f"Schritt {i}")),
                description=str(item.get("description", "")),
                estimated_minutes=int(item.get("estimated_minutes", 15)),
                order=i,
            ))

        return subtasks

    async def confirm_breakdown(
        self,
        task_id: UUID,
        user_id: UUID,
        subtasks: list[BreakdownConfirmSubtask],
    ) -> BreakdownConfirmResponse:
        """Create confirmed sub-tasks for a parent task."""
        task = await self._get_task_with_checks(task_id, user_id)

        # Set parent task to in_progress
        task.status = TaskStatus.IN_PROGRESS

        created_tasks = []
        for subtask_data in subtasks:
            sub_task = Task(
                user_id=user_id,
                title=subtask_data.title,
                description=subtask_data.description,
                priority=task.priority,
                parent_id=task.id,
                estimated_minutes=subtask_data.estimated_minutes,
                source=TaskSource.BREAKDOWN,
                tags=task.tags,
            )
            self.db.add(sub_task)
            created_tasks.append(sub_task)

        await self.db.flush()
        for sub in created_tasks:
            await self.db.refresh(sub)

        return BreakdownConfirmResponse(
            parent_task=BreakdownConfirmParent(
                id=task.id,
                title=task.title,
                status=task.status.value,
            ),
            created_subtasks=[TaskResponse.model_validate(t) for t in created_tasks],
        )
