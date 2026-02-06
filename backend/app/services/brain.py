"""Brain service for managing Second Brain entries."""

from uuid import UUID

from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BrainEntryNotFoundError, SearchUnavailableError
from app.models.brain_entry import BrainEntry, BrainEntryType
from app.schemas.brain import BrainEntryCreate, BrainEntryUpdate, BrainEntryResponse, BrainSearchResult


class BrainService:
    """Service for brain entry operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(self, user_id: UUID, data: BrainEntryCreate) -> BrainEntry:
        """Create a new brain entry."""
        entry = BrainEntry(
            user_id=user_id,
            title=data.title,
            content=data.content,
            entry_type=BrainEntryType(data.entry_type) if data.entry_type else BrainEntryType.MANUAL,
            tags=data.tags or [],
            source_url=data.source_url,
        )

        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)

        return entry

    async def get_entry(self, entry_id: UUID, user_id: UUID) -> BrainEntry:
        """Get a brain entry by ID with ownership check."""
        result = await self.db.execute(
            select(BrainEntry).where(
                BrainEntry.id == entry_id,
                BrainEntry.user_id == user_id,
            )
        )
        entry = result.scalar_one_or_none()

        if not entry:
            raise BrainEntryNotFoundError(entry_id=str(entry_id))

        return entry

    async def get_entries(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
        entry_type: str | None = None,
        tags: list[str] | None = None,
    ) -> tuple[list[BrainEntry], UUID | None, bool, int]:
        """Get paginated brain entries for a user with optional filters."""
        query = select(BrainEntry).where(
            BrainEntry.user_id == user_id
        ).order_by(desc(BrainEntry.updated_at), desc(BrainEntry.id))

        count_query = select(func.count()).select_from(BrainEntry).where(
            BrainEntry.user_id == user_id
        )

        if entry_type:
            et = BrainEntryType(entry_type)
            query = query.where(BrainEntry.entry_type == et)
            count_query = count_query.where(BrainEntry.entry_type == et)

        if tags:
            query = query.where(BrainEntry.tags.overlap(tags))
            count_query = count_query.where(BrainEntry.tags.overlap(tags))

        if cursor:
            cursor_result = await self.db.execute(
                select(BrainEntry.updated_at, BrainEntry.id).where(BrainEntry.id == cursor)
            )
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_updated_at, cursor_id = cursor_row
                query = query.where(
                    or_(
                        BrainEntry.updated_at < cursor_updated_at,
                        and_(
                            BrainEntry.updated_at == cursor_updated_at,
                            BrainEntry.id < cursor_id,
                        ),
                    )
                )

        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        has_more = len(entries) > limit
        if has_more:
            entries = entries[:limit]

        next_cursor = entries[-1].id if entries and has_more else None

        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        return entries, next_cursor, has_more, total_count

    async def update_entry(self, entry_id: UUID, user_id: UUID, data: BrainEntryUpdate) -> BrainEntry:
        """Update a brain entry."""
        entry = await self.get_entry(entry_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        await self.db.flush()
        await self.db.refresh(entry)

        return entry

    async def delete_entry(self, entry_id: UUID, user_id: UUID) -> None:
        """Delete a brain entry."""
        entry = await self.get_entry(entry_id, user_id)
        await self.db.delete(entry)
        await self.db.flush()

    async def search(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[BrainSearchResult]:
        """
        Search brain entries using ILIKE text search (Phase 2 fallback).

        Embedding-based vector search will be added later when
        sentence-transformers is available.
        """
        try:
            search_pattern = f"%{query}%"

            result = await self.db.execute(
                select(BrainEntry).where(
                    BrainEntry.user_id == user_id,
                    or_(
                        BrainEntry.title.ilike(search_pattern),
                        BrainEntry.content.ilike(search_pattern),
                    ),
                ).order_by(desc(BrainEntry.updated_at)).limit(limit)
            )
            entries = result.scalars().all()

            results = []
            for entry in entries:
                # Simple relevance scoring based on match location
                title_match = query.lower() in entry.title.lower()
                score = 0.9 if title_match else 0.6

                # Extract matching chunks
                matched_chunks = []
                content_lower = entry.content.lower()
                query_lower = query.lower()
                idx = content_lower.find(query_lower)
                if idx != -1:
                    start = max(0, idx - 50)
                    end = min(len(entry.content), idx + len(query) + 50)
                    matched_chunks.append(entry.content[start:end])

                if score >= min_score:
                    results.append(BrainSearchResult(
                        entry=BrainEntryResponse.model_validate(entry),
                        score=score,
                        matched_chunks=matched_chunks,
                    ))

            return results
        except Exception as e:
            raise SearchUnavailableError(detail=f"Search failed: {str(e)}")
