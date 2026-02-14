"""n8n Bridge API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.n8n import (
    N8nExecuteRequest, N8nExecuteResponse, N8nWorkflowCreate,
    N8nWorkflowListResponse, N8nWorkflowResponse, N8nWorkflowUpdate,
)
from app.services.n8n_bridge import N8nBridgeService

router = APIRouter(tags=["n8n"])


@router.get("/workflows", response_model=N8nWorkflowListResponse)
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.n8n_workflow import N8nWorkflow

    service = N8nBridgeService(db)
    workflows, total = await service.list_workflows(str(current_user.id))

    def to_response(w: N8nWorkflow) -> N8nWorkflowResponse:
        return N8nWorkflowResponse(
            id=str(w.id),
            user_id=str(w.user_id),
            name=w.name,
            description=w.description,
            webhook_url=w.webhook_url,
            input_schema=w.input_schema,
            is_active=w.is_active,
            execution_count=w.execution_count,
            last_executed_at=w.last_executed_at,
            created_at=w.created_at,
        )

    return N8nWorkflowListResponse(
        workflows=[to_response(w) for w in workflows],
        total=total,
    )


@router.post("/workflows", response_model=N8nWorkflowResponse, status_code=201)
async def create_workflow(
    body: N8nWorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    workflow = await service.register_workflow(
        str(current_user.id), body.name, body.webhook_url,
        body.description, body.input_schema,
    )
    await db.commit()

    return N8nWorkflowResponse(
        id=str(workflow.id),
        user_id=str(workflow.user_id),
        name=workflow.name,
        description=workflow.description,
        webhook_url=workflow.webhook_url,
        input_schema=workflow.input_schema,
        is_active=workflow.is_active,
        execution_count=workflow.execution_count,
        last_executed_at=workflow.last_executed_at,
        created_at=workflow.created_at,
    )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    deleted = await service.delete_workflow(str(current_user.id), str(workflow_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.commit()
    return {"message": "Workflow deleted"}


@router.post("/workflows/{workflow_id}/execute", response_model=N8nExecuteResponse)
async def execute_workflow(
    workflow_id: UUID,
    body: N8nExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = N8nBridgeService(db)
    result = await service.execute_workflow(str(current_user.id), str(workflow_id), body.input_data)
    await db.commit()

    if "error" in result and not result.get("success"):
        raise HTTPException(status_code=404, detail=result["error"])

    return N8nExecuteResponse(
        workflow_id=str(workflow_id),
        success=result.get("success", False),
        response_data=result.get("response_data", {}),
        execution_count=result.get("execution_count", 0),
    )
