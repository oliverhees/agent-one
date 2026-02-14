"""Webhook API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate, WebhookListResponse, WebhookLogListResponse,
    WebhookLogResponse, WebhookResponse, WebhookUpdate,
)
from app.services.webhook import WebhookService

router = APIRouter(tags=["Webhooks"])


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.webhook import WebhookConfig

    service = WebhookService(db)
    webhooks, total = await service.list_webhooks(str(current_user.id))

    def to_response(w: WebhookConfig) -> WebhookResponse:
        return WebhookResponse(
            id=str(w.id),
            user_id=str(w.user_id),
            name=w.name,
            url=w.url,
            direction=w.direction,
            events=w.events,
            is_active=w.is_active,
            created_at=w.created_at,
        )

    return WebhookListResponse(
        webhooks=[to_response(w) for w in webhooks],
        total=total,
    )


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    webhook = await service.create_webhook(
        str(current_user.id), body.name, body.url, body.direction, body.events,
    )
    await db.commit()

    return WebhookResponse(
        id=str(webhook.id),
        user_id=str(webhook.user_id),
        name=webhook.name,
        url=webhook.url,
        direction=webhook.direction,
        events=webhook.events,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebhookService(db)
    deleted = await service.delete_webhook(str(current_user.id), str(webhook_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()
    return {"message": "Webhook deleted"}


@router.get("/{webhook_id}/logs", response_model=WebhookLogListResponse)
async def get_webhook_logs(
    webhook_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.webhook import WebhookLog

    service = WebhookService(db)
    logs, total = await service.get_logs(str(current_user.id), str(webhook_id), limit)

    def to_response(l: WebhookLog) -> WebhookLogResponse:
        return WebhookLogResponse(
            id=str(l.id),
            webhook_id=str(l.webhook_id),
            direction=l.direction,
            event_type=l.event_type,
            payload=l.payload,
            status_code=l.status_code,
            attempt=l.attempt,
            success=l.success,
            created_at=l.created_at,
        )

    return WebhookLogListResponse(
        logs=[to_response(l) for l in logs],
        total=total,
    )


@router.post("/incoming/{webhook_id}")
async def incoming_webhook(
    webhook_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for receiving incoming webhooks (no auth required)."""
    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.json()

    service = WebhookService(db)
    result = await service.process_incoming(str(webhook_id), body, signature)
    await db.commit()

    status = result.pop("status", 200)
    if status != 200:
        raise HTTPException(status_code=status, detail=result.get("error", "Error"))
    return result
