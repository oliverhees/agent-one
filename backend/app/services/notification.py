"""Notification service for sending Expo push notifications."""

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
EXPO_BATCH_LIMIT = 100


@dataclass
class PushNotification:
    """A single push notification to send via Expo."""

    to: str
    title: str
    body: str
    data: dict = field(default_factory=dict)
    sound: str = "default"
    channel_id: str = "alice-notifications"


class NotificationService:
    """Service for sending push notifications via the Expo Push API."""

    @staticmethod
    async def send_notification(notification: PushNotification) -> bool:
        """Send a single push notification. Returns True on success."""
        payload = {
            "to": notification.to,
            "title": notification.title,
            "body": notification.body,
            "data": notification.data,
            "sound": notification.sound,
            "channelId": notification.channel_id,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    EXPO_PUSH_URL,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                result = response.json()
                data = result.get("data", {})

                if data.get("status") == "error":
                    logger.warning(
                        "Expo push error for token %s: %s",
                        notification.to[:20],
                        data.get("message", "unknown"),
                    )
                    return False

                logger.debug("Push notification sent to %s", notification.to[:20])
                return True

        except httpx.HTTPError as e:
            logger.error("HTTP error sending push notification: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error sending push notification: %s", e)
            return False

    @staticmethod
    async def send_bulk_notifications(notifications: list[PushNotification]) -> int:
        """Send multiple push notifications in batches. Returns count of successful sends."""
        if not notifications:
            return 0

        success_count = 0

        for i in range(0, len(notifications), EXPO_BATCH_LIMIT):
            batch = notifications[i : i + EXPO_BATCH_LIMIT]
            payloads = [
                {
                    "to": n.to,
                    "title": n.title,
                    "body": n.body,
                    "data": n.data,
                    "sound": n.sound,
                    "channelId": n.channel_id,
                }
                for n in batch
            ]

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        EXPO_PUSH_URL,
                        json=payloads,
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                    )
                    response.raise_for_status()

                    result = response.json()
                    for item in result.get("data", []):
                        if item.get("status") == "ok":
                            success_count += 1

            except httpx.HTTPError as e:
                logger.error("HTTP error sending bulk push notifications: %s", e)
            except Exception as e:
                logger.error("Unexpected error sending bulk push notifications: %s", e)

        logger.info(
            "Bulk push: %d/%d notifications sent successfully",
            success_count,
            len(notifications),
        )
        return success_count
