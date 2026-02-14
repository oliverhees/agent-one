"""Trust service for progressive agent autonomy."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trust_score import TrustScore

ESCALATION_THRESHOLD = 10
READ_ACTIONS = {"read", "list", "search", "summarize", "analyze"}
WRITE_ACTIONS = {"write", "send", "create", "update", "delete", "draft"}


class TrustService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_score(self, user_id: str, agent_type: str, action_type: str) -> TrustScore:
        stmt = select(TrustScore).where(
            TrustScore.user_id == UUID(user_id),
            TrustScore.agent_type == agent_type,
            TrustScore.action_type == action_type,
        )
        result = await self.db.execute(stmt)
        score = result.scalar_one_or_none()
        if not score:
            score = TrustScore(
                user_id=UUID(user_id),
                agent_type=agent_type,
                action_type=action_type,
                trust_level=1,
                successful_actions=0,
                total_actions=0,
            )
            self.db.add(score)
            await self.db.flush()
            await self.db.refresh(score)
        return score

    async def get_trust_level(self, user_id: str, agent_type: str, action_type: str) -> int:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        return score.trust_level

    async def requires_approval(self, user_id: str, agent_type: str, action_type: str) -> bool:
        level = await self.get_trust_level(user_id, agent_type, action_type)
        if level >= 3:
            return False
        if level >= 2 and action_type in READ_ACTIONS:
            return False
        return True

    async def record_action(self, user_id: str, agent_type: str, action_type: str, success: bool) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        score.total_actions += 1
        if success:
            score.successful_actions += 1
        if score.trust_level == 1 and score.successful_actions >= ESCALATION_THRESHOLD:
            score.trust_level = 2
            score.last_escalation_at = datetime.now(timezone.utc)
        await self.db.flush()
        return score

    async def set_trust_level(self, user_id: str, agent_type: str, action_type: str, level: int) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        old_level = score.trust_level
        score.trust_level = max(1, min(3, level))
        if score.trust_level > old_level:
            score.last_escalation_at = datetime.now(timezone.utc)
        await self.db.flush()
        return score

    async def record_violation(self, user_id: str, agent_type: str, action_type: str) -> TrustScore:
        score = await self.get_or_create_score(user_id, agent_type, action_type)
        score.last_violation_at = datetime.now(timezone.utc)
        if score.trust_level == 3:
            score.trust_level = 2
        await self.db.flush()
        return score

    async def get_all_scores(self, user_id: str) -> list[TrustScore]:
        stmt = select(TrustScore).where(TrustScore.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
