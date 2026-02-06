"""Proactive service for managing mentioned items extracted from chat."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    MentionedItemNotFoundError,
    MentionedItemAlreadyConvertedError,
)
from app.models.mentioned_item import MentionedItem, MentionedItemStatus, MentionedItemType
from app.models.task import Task, TaskPriority
from app.models.brain_entry import BrainEntry, BrainEntryType
from app.schemas.proactive import MentionedItemConvertRequest


class ProactiveService:
    """Service for proactive mentioned item operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_mentioned_items(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
        status: str | None = None,
        item_type: str | None = None,
    ) -> tuple[list[MentionedItem], UUID | None, bool, int]:
        """Get paginated mentioned items for a user."""
        query = select(MentionedItem).where(
            MentionedItem.user_id == user_id
        ).order_by(desc(MentionedItem.created_at), desc(MentionedItem.id))

        count_query = select(func.count()).select_from(MentionedItem).where(
            MentionedItem.user_id == user_id
        )

        if status:
            item_status = MentionedItemStatus(status)
            query = query.where(MentionedItem.status == item_status)
            count_query = count_query.where(MentionedItem.status == item_status)

        if item_type:
            it = MentionedItemType(item_type)
            query = query.where(MentionedItem.item_type == it)
            count_query = count_query.where(MentionedItem.item_type == it)

        if cursor:
            cursor_result = await self.db.execute(
                select(MentionedItem.created_at, MentionedItem.id).where(
                    MentionedItem.id == cursor
                )
            )
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_created_at, cursor_id = cursor_row
                query = query.where(
                    or_(
                        MentionedItem.created_at < cursor_created_at,
                        and_(
                            MentionedItem.created_at == cursor_created_at,
                            MentionedItem.id < cursor_id,
                        ),
                    )
                )

        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        next_cursor = items[-1].id if items and has_more else None

        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        return items, next_cursor, has_more, total_count

    async def _get_item(self, item_id: UUID, user_id: UUID) -> MentionedItem:
        """Get a mentioned item by ID with ownership check."""
        result = await self.db.execute(
            select(MentionedItem).where(
                MentionedItem.id == item_id,
                MentionedItem.user_id == user_id,
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise MentionedItemNotFoundError(item_id=str(item_id))

        return item

    async def convert_item(
        self, item_id: UUID, user_id: UUID, convert_to: str
    ) -> MentionedItem:
        """Convert a mentioned item to a task or brain entry."""
        item = await self._get_item(item_id, user_id)

        if item.status == MentionedItemStatus.CONVERTED:
            raise MentionedItemAlreadyConvertedError(item_id=str(item_id))

        extracted = item.extracted_data or {}

        if convert_to == "task":
            task = Task(
                user_id=user_id,
                title=extracted.get("suggested_title", item.content[:500]),
                description=item.content,
                priority=TaskPriority(extracted.get("priority", "medium")),
                tags=extracted.get("tags", []),
                source="chat_extract",
            )
            self.db.add(task)
            await self.db.flush()
            await self.db.refresh(task)

            item.converted_to_id = task.id
            item.converted_to_type = "task"

        elif convert_to == "brain_entry":
            entry = BrainEntry(
                user_id=user_id,
                title=extracted.get("suggested_title", item.content[:500]),
                content=item.content,
                entry_type=BrainEntryType.CHAT_EXTRACT,
                tags=extracted.get("tags", []),
            )
            self.db.add(entry)
            await self.db.flush()
            await self.db.refresh(entry)

            item.converted_to_id = entry.id
            item.converted_to_type = "brain_entry"

        item.status = MentionedItemStatus.CONVERTED

        await self.db.flush()
        await self.db.refresh(item)

        return item

    async def dismiss_item(self, item_id: UUID, user_id: UUID) -> MentionedItem:
        """Dismiss a mentioned item."""
        item = await self._get_item(item_id, user_id)

        item.status = MentionedItemStatus.DISMISSED

        await self.db.flush()
        await self.db.refresh(item)

        return item

    async def snooze_item(
        self, item_id: UUID, user_id: UUID, until: datetime
    ) -> MentionedItem:
        """Snooze a mentioned item until a specified time."""
        item = await self._get_item(item_id, user_id)

        item.status = MentionedItemStatus.SNOOZED
        item.snoozed_until = until

        await self.db.flush()
        await self.db.refresh(item)

        return item
