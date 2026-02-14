"""Webhook service for incoming/outgoing webhook management."""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_value, decrypt_value
from app.models.webhook import WebhookConfig, WebhookLog

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF = [1, 4, 16]


class WebhookService:
    """Service for managing and executing webhooks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_secret() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature[7:], expected)

    @staticmethod
    def compute_signature(payload: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    async def create_webhook(self, user_id: str, name: str, url: str, direction: str, events: list[str] | None = None) -> WebhookConfig:
        secret = self.generate_secret()
        webhook = WebhookConfig(
            user_id=UUID(user_id),
            name=name,
            url=url,
            secret=encrypt_value(secret),
            direction=direction,
            events=events or [],
            is_active=True,
        )
        self.db.add(webhook)
        await self.db.flush()
        await self.db.refresh(webhook)
        return webhook

    async def list_webhooks(self, user_id: str) -> tuple[list[WebhookConfig], int]:
        count_stmt = select(func.count()).select_from(WebhookConfig).where(WebhookConfig.user_id == UUID(user_id))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(WebhookConfig).where(WebhookConfig.user_id == UUID(user_id)).order_by(WebhookConfig.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_webhook(self, user_id: str, webhook_id: str) -> WebhookConfig | None:
        stmt = select(WebhookConfig).where(WebhookConfig.id == UUID(webhook_id), WebhookConfig.user_id == UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_webhook(self, user_id: str, webhook_id: str) -> bool:
        webhook = await self.get_webhook(user_id, webhook_id)
        if not webhook:
            return False
        await self.db.delete(webhook)
        await self.db.flush()
        return True

    async def process_incoming(self, webhook_id: str, payload: dict, signature: str) -> dict:
        """Process an incoming webhook request."""
        stmt = select(WebhookConfig).where(WebhookConfig.id == UUID(webhook_id), WebhookConfig.is_active == True)
        result = await self.db.execute(stmt)
        webhook = result.scalar_one_or_none()

        if not webhook:
            return {"error": "Webhook not found or inactive", "status": 404}

        secret = decrypt_value(webhook.secret)
        payload_bytes = json.dumps(payload).encode()

        if not self.verify_signature(payload_bytes, signature, secret):
            log = WebhookLog(
                webhook_id=webhook.id, direction="incoming",
                event_type=payload.get("event", "unknown"),
                payload=payload, success=False, attempt=1,
            )
            self.db.add(log)
            await self.db.flush()
            return {"error": "Invalid signature", "status": 401}

        log = WebhookLog(
            webhook_id=webhook.id, direction="incoming",
            event_type=payload.get("event", "unknown"),
            payload=payload, success=True, status_code=200, attempt=1,
        )
        self.db.add(log)
        await self.db.flush()

        return {"status": 200, "message": "Webhook received", "event": payload.get("event")}

    async def send_outgoing(self, event_type: str, event_data: dict, user_id: str) -> int:
        """Send outgoing webhook to all matching configs. Returns count of successful sends."""
        stmt = select(WebhookConfig).where(
            WebhookConfig.user_id == UUID(user_id),
            WebhookConfig.direction == "outgoing",
            WebhookConfig.is_active == True,
        )
        result = await self.db.execute(stmt)
        webhooks = result.scalars().all()

        success_count = 0
        for webhook in webhooks:
            events_list = webhook.events if isinstance(webhook.events, list) else []
            if event_type not in events_list:
                continue

            secret = decrypt_value(webhook.secret)
            payload = {"event": event_type, "data": event_data, "timestamp": datetime.now(timezone.utc).isoformat()}
            payload_bytes = json.dumps(payload).encode()
            signature = self.compute_signature(payload_bytes, secret)

            for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            webhook.url,
                            content=payload_bytes,
                            headers={
                                "Content-Type": "application/json",
                                "X-Webhook-Signature": signature,
                            },
                        )

                    log = WebhookLog(
                        webhook_id=webhook.id, direction="outgoing",
                        event_type=event_type, payload=payload,
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else None,
                        attempt=attempt, success=response.is_success,
                    )
                    self.db.add(log)

                    if response.is_success:
                        success_count += 1
                        break
                except Exception as e:
                    log = WebhookLog(
                        webhook_id=webhook.id, direction="outgoing",
                        event_type=event_type, payload=payload,
                        response_body=str(e)[:1000],
                        attempt=attempt, success=False,
                    )
                    self.db.add(log)

            await self.db.flush()

        return success_count

    async def get_logs(self, user_id: str, webhook_id: str, limit: int = 50) -> tuple[list[WebhookLog], int]:
        webhook = await self.get_webhook(user_id, webhook_id)
        if not webhook:
            return [], 0

        count_stmt = select(func.count()).select_from(WebhookLog).where(WebhookLog.webhook_id == webhook.id)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(WebhookLog).where(WebhookLog.webhook_id == webhook.id).order_by(WebhookLog.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
