"""Nudge service for managing ADHS reminders."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NudgeNotFoundError, NudgeAlreadyAcknowledgedError
from app.models.nudge_history import NudgeHistory, NudgeType
from app.models.task import Task
from app.schemas.nudge import (
    NudgeResponse,
    NudgeListResponse,
    NudgeAcknowledgeResponse,
    NudgeHistoryItem,
    NudgeHistoryResponse,
)


# Map integer nudge_level to human-readable strings
NUDGE_LEVEL_NAMES = {1: "gentle", 2: "moderate", 3: "firm"}
# Map NudgeType enum to API-facing type strings
NUDGE_TYPE_MAP = {
    NudgeType.DEADLINE: "deadline_approaching",
    NudgeType.FOLLOW_UP: "follow_up",
    NudgeType.STREAK_REMINDER: "stale",
    NudgeType.MOTIVATIONAL: "overdue",
}


class NudgeService:
    """Service for nudge operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_nudge_response(self, nudge: NudgeHistory, task_title: str | None = None) -> NudgeResponse:
        """Convert a NudgeHistory model to a NudgeResponse."""
        return NudgeResponse(
            id=nudge.id,
            task_id=nudge.task_id,
            task_title=task_title,
            nudge_level=NUDGE_LEVEL_NAMES.get(nudge.nudge_level, "gentle"),
            nudge_type=NUDGE_TYPE_MAP.get(nudge.nudge_type, nudge.nudge_type.value),
            message=nudge.message,
            delivered_at=nudge.delivered_at,
        )

    async def get_active_nudges(self, user_id: UUID) -> NudgeListResponse:
        """Get all unacknowledged nudges for a user."""
        result = await self.db.execute(
            select(NudgeHistory, Task.title)
            .outerjoin(Task, NudgeHistory.task_id == Task.id)
            .where(
                NudgeHistory.user_id == user_id,
                NudgeHistory.acknowledged_at.is_(None),
            )
            .order_by(desc(NudgeHistory.delivered_at))
        )
        rows = result.all()

        nudges = [self._to_nudge_response(nudge, task_title) for nudge, task_title in rows]

        return NudgeListResponse(
            nudges=nudges,
            count=len(nudges),
        )

    async def acknowledge_nudge(self, nudge_id: UUID, user_id: UUID) -> NudgeAcknowledgeResponse:
        """Acknowledge a nudge."""
        result = await self.db.execute(
            select(NudgeHistory).where(
                NudgeHistory.id == nudge_id,
                NudgeHistory.user_id == user_id,
            )
        )
        nudge = result.scalar_one_or_none()

        if not nudge:
            raise NudgeNotFoundError(nudge_id=str(nudge_id))

        if nudge.acknowledged_at is not None:
            raise NudgeAlreadyAcknowledgedError(nudge_id=str(nudge_id))

        now = datetime.now(timezone.utc)
        nudge.acknowledged_at = now

        await self.db.flush()

        return NudgeAcknowledgeResponse(
            id=nudge.id,
            acknowledged_at=now,
        )

    async def get_history(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 50,
    ) -> NudgeHistoryResponse:
        """Get paginated nudge history."""
        query = (
            select(NudgeHistory, Task.title)
            .outerjoin(Task, NudgeHistory.task_id == Task.id)
            .where(NudgeHistory.user_id == user_id)
            .order_by(desc(NudgeHistory.delivered_at), desc(NudgeHistory.id))
        )

        count_query = select(func.count()).select_from(NudgeHistory).where(
            NudgeHistory.user_id == user_id
        )

        if cursor:
            cursor_result = await self.db.execute(
                select(NudgeHistory.delivered_at, NudgeHistory.id).where(NudgeHistory.id == cursor)
            )
            cursor_row = cursor_result.one_or_none()
            if cursor_row:
                from sqlalchemy import or_, and_
                cursor_delivered_at, cursor_id = cursor_row
                query = query.where(
                    or_(
                        NudgeHistory.delivered_at < cursor_delivered_at,
                        and_(
                            NudgeHistory.delivered_at == cursor_delivered_at,
                            NudgeHistory.id < cursor_id,
                        ),
                    )
                )

        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        rows = list(result.all())

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        items = []
        for nudge, task_title in rows:
            items.append(NudgeHistoryItem(
                id=nudge.id,
                task_id=nudge.task_id,
                task_title=task_title,
                nudge_level=NUDGE_LEVEL_NAMES.get(nudge.nudge_level, "gentle"),
                nudge_type=NUDGE_TYPE_MAP.get(nudge.nudge_type, nudge.nudge_type.value),
                message=nudge.message,
                delivered_at=nudge.delivered_at,
                acknowledged_at=nudge.acknowledged_at,
            ))

        next_cursor = str(items[-1].id) if items and has_more else None

        return NudgeHistoryResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            total_count=total_count,
        )

    async def create_nudge(
        self,
        user_id: UUID,
        task_id: UUID | None,
        level: int,
        nudge_type: NudgeType,
        message: str,
    ) -> NudgeHistory:
        """Create a new nudge."""
        nudge = NudgeHistory(
            user_id=user_id,
            task_id=task_id,
            nudge_level=level,
            nudge_type=nudge_type,
            message=message,
        )
        self.db.add(nudge)
        await self.db.flush()
        await self.db.refresh(nudge)
        return nudge
