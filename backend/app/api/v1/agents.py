"""Agent system API endpoints — trust, approvals, email config, activity."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.user import User
from app.schemas.agent import (
    TrustOverview,
    TrustScoreResponse,
    TrustUpdateRequest,
    ApprovalDecision,
    ApprovalRequestResponse,
    EmailConfigCreate,
    EmailConfigResponse,
)
from app.services.trust import TrustService

router = APIRouter(tags=["Agents"])


@router.get("/trust", response_model=TrustOverview)
async def get_trust_scores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all trust scores for the current user."""
    service = TrustService(db)
    scores = await service.get_all_scores(str(current_user.id))
    return TrustOverview(
        scores=[TrustScoreResponse.model_validate(s) for s in scores]
    )


@router.put("/trust", status_code=status.HTTP_200_OK)
async def set_trust_level(
    data: TrustUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set trust level for an agent type (applies to all action types)."""
    service = TrustService(db)
    for action_type in ["read", "write", "send", "delete"]:
        await service.set_trust_level(str(current_user.id), data.agent_type, action_type, data.trust_level)
    await db.commit()
    return {"status": "updated", "agent_type": data.agent_type, "trust_level": data.trust_level}


@router.get("/approvals/pending", response_model=list[ApprovalRequestResponse])
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending approval requests for the current user."""
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.user_id == current_user.id,
        ApprovalRequest.status == ApprovalStatus.PENDING,
    ).order_by(ApprovalRequest.created_at.desc())
    result = await db.execute(stmt)
    return [ApprovalRequestResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/approve/{approval_id}")
async def approve_action(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pending action."""
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.user_id == current_user.id,
        ApprovalRequest.status == ApprovalStatus.PENDING,
    )
    result = await db.execute(stmt)
    request = result.scalar_one_or_none()
    if not request:
        return {"error": "Approval request not found or already resolved"}

    request.status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED
    request.user_reason = decision.reason
    await db.commit()

    trust_service = TrustService(db)
    if decision.approved:
        await trust_service.record_action(str(current_user.id), request.agent_type, request.action, success=True)
    else:
        await trust_service.record_violation(str(current_user.id), request.agent_type, request.action)
    await db.commit()

    return {"status": request.status.value, "approval_id": str(approval_id)}


@router.post("/email/config", response_model=EmailConfigResponse)
async def save_email_config(
    data: EmailConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save email configuration (SMTP/IMAP)."""
    from app.services.email import EmailService
    service = EmailService(db)
    config = await service.save_config(
        user_id=str(current_user.id),
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_user=data.smtp_user,
        smtp_password=data.smtp_password,
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        imap_user=data.imap_user,
        imap_password=data.imap_password,
    )
    await db.commit()
    return EmailConfigResponse.model_validate(config)


@router.get("/email/config", response_model=EmailConfigResponse | None)
async def get_email_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get email configuration for the current user."""
    from app.services.email import EmailService
    service = EmailService(db)
    config = await service.get_config(str(current_user.id))
    if not config:
        return None
    return EmailConfigResponse.model_validate(config)
