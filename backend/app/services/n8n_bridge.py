"""n8n Bridge service for workflow registration and execution."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.n8n_workflow import N8nWorkflow

logger = logging.getLogger(__name__)


class N8nBridgeService:
    """Service for managing and executing n8n workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_workflow(self, user_id: str, name: str, webhook_url: str, description: str | None = None, input_schema: dict | None = None) -> N8nWorkflow:
        workflow = N8nWorkflow(
            user_id=UUID(user_id),
            name=name,
            description=description,
            webhook_url=webhook_url,
            input_schema=input_schema or {},
            is_active=True,
        )
        self.db.add(workflow)
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def list_workflows(self, user_id: str) -> tuple[list[N8nWorkflow], int]:
        count_stmt = select(func.count()).select_from(N8nWorkflow).where(N8nWorkflow.user_id == UUID(user_id))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(N8nWorkflow).where(N8nWorkflow.user_id == UUID(user_id)).order_by(N8nWorkflow.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_workflow(self, user_id: str, workflow_id: str) -> N8nWorkflow | None:
        stmt = select(N8nWorkflow).where(N8nWorkflow.id == UUID(workflow_id), N8nWorkflow.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def execute_workflow(self, user_id: str, workflow_id: str, input_data: dict[str, Any] | None = None) -> dict:
        workflow = await self.get_workflow(user_id, workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found"}

        if not workflow.is_active:
            return {"success": False, "error": "Workflow is inactive"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    workflow.webhook_url,
                    json=input_data or {},
                    headers={"Content-Type": "application/json"},
                )

            workflow.execution_count += 1
            workflow.last_executed_at = datetime.now(timezone.utc)
            await self.db.flush()

            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw": response.text[:1000]},
                "execution_count": workflow.execution_count,
            }
        except Exception as e:
            logger.error("n8n workflow execution failed: %s", e)
            workflow.execution_count += 1
            workflow.last_executed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return {"success": False, "error": str(e), "execution_count": workflow.execution_count}

    async def delete_workflow(self, user_id: str, workflow_id: str) -> bool:
        workflow = await self.get_workflow(user_id, workflow_id)
        if not workflow:
            return False
        await self.db.delete(workflow)
        await self.db.flush()
        return True
