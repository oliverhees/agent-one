"""Task service for managing user tasks."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TaskNotFoundError, TaskAlreadyCompletedError
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service for task operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _resolve_priority(value: str | None) -> TaskPriority:
        """Resolve priority string to enum, validating the value."""
        if not value:
            return TaskPriority.MEDIUM
        # Validate the value is a known priority
        return TaskPriority(value)

    @staticmethod
    def _resolve_status(value: str | None) -> TaskStatus:
        """Resolve status string to enum, validating the value."""
        if not value:
            return TaskStatus.OPEN
        return TaskStatus(value)

    async def create_task(self, user_id: UUID, data: TaskCreate) -> Task:
        """Create a new task."""
        priority = self._resolve_priority(data.priority)
        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            priority=priority,
            due_date=data.due_date,
            tags=data.tags or [],
            parent_id=data.parent_id,
            estimated_minutes=data.estimated_minutes,
        )

        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def get_task(self, task_id: UUID, user_id: UUID) -> Task:
        """Get a task by ID with ownership check."""
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id,
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id=str(task_id))

        return task

    async def get_tasks(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
        status: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
    ) -> tuple[list[Task], UUID | None, bool, int]:
        """Get paginated tasks for a user with optional filters."""
        # Base query
        query = select(Task).where(
            Task.user_id == user_id
        ).order_by(desc(Task.updated_at), desc(Task.id))

        # Count query (with same filters)
        count_query = select(func.count()).select_from(Task).where(
            Task.user_id == user_id
        )

        # Apply filters
        if status:
            task_status = TaskStatus(status)
            query = query.where(Task.status == task_status)
            count_query = count_query.where(Task.status == task_status)

        if priority:
            task_priority = TaskPriority(priority)
            query = query.where(Task.priority == task_priority)
            count_query = count_query.where(Task.priority == task_priority)

        if tags:
            query = query.where(Task.tags.overlap(tags))
            count_query = count_query.where(Task.tags.overlap(tags))

        # Cursor pagination
        if cursor:
            cursor_result = await self.db.execute(
                select(Task.updated_at, Task.id).where(Task.id == cursor)
            )
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_updated_at, cursor_id = cursor_row
                query = query.where(
                    or_(
                        Task.updated_at < cursor_updated_at,
                        and_(
                            Task.updated_at == cursor_updated_at,
                            Task.id < cursor_id,
                        ),
                    )
                )

        # Fetch limit+1 to check for more
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        tasks = list(result.scalars().all())

        has_more = len(tasks) > limit
        if has_more:
            tasks = tasks[:limit]

        next_cursor = tasks[-1].id if tasks and has_more else None

        # Total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        return tasks, next_cursor, has_more, total_count

    async def get_today_tasks(self, user_id: UUID) -> list[Task]:
        """Get tasks due today or currently in progress."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                or_(
                    and_(
                        Task.due_date >= today_start,
                        Task.due_date <= today_end,
                    ),
                    and_(
                        Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
                        Task.due_date <= today_end,
                        Task.due_date.is_not(None),
                    ),
                ),
            ).order_by(Task.due_date.asc().nullslast(), Task.priority.desc())
        )
        return list(result.scalars().all())

    async def update_task(self, task_id: UUID, user_id: UUID, data: TaskUpdate) -> Task:
        """Update a task."""
        task = await self.get_task(task_id, user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "priority" in update_data and update_data["priority"] is not None:
            update_data["priority"] = TaskPriority(update_data["priority"])

        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = TaskStatus(update_data["status"])

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        """Delete a task."""
        task = await self.get_task(task_id, user_id)
        await self.db.delete(task)
        await self.db.flush()

    async def complete_task(
        self, task_id: UUID, user_id: UUID
    ) -> tuple[Task, int, int, int, bool]:
        """
        Complete a task and calculate XP.

        Returns:
            tuple: (task, xp_earned, total_xp, level, level_up)
        """
        task = await self.get_task(task_id, user_id)

        if task.status == TaskStatus.DONE:
            raise TaskAlreadyCompletedError(task_id=str(task_id))

        # XP calculation
        base_xp_map = {
            TaskPriority.LOW: 10,
            TaskPriority.MEDIUM: 25,
            TaskPriority.HIGH: 50,
            TaskPriority.URGENT: 100,
        }
        base_xp = base_xp_map.get(task.priority, 25)

        # Bonus: completed on time (before or on due_date)
        now = datetime.now(timezone.utc)
        if task.due_date and now <= task.due_date:
            base_xp = int(base_xp * 1.5)  # +50%

        xp_earned = base_xp

        # Update task
        task.status = TaskStatus.DONE
        task.completed_at = now
        task.xp_earned = xp_earned

        await self.db.flush()
        await self.db.refresh(task)

        # Calculate total XP for user (simplified - sum all completed tasks)
        xp_result = await self.db.execute(
            select(func.coalesce(func.sum(Task.xp_earned), 0)).where(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE,
            )
        )
        total_xp = xp_result.scalar_one()

        # Simple level calculation: level = total_xp / 100 + 1
        level = int(total_xp / 100) + 1
        previous_level = int((total_xp - xp_earned) / 100) + 1
        level_up = level > previous_level

        return task, xp_earned, total_xp, level, level_up
