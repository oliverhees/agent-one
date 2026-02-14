"""SSE streaming endpoint for agent activity feed."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agent Stream"])

# In-memory event queues per user (production: use Redis pub/sub)
_user_queues: dict[str, asyncio.Queue] = {}


def get_user_queue(user_id: str) -> asyncio.Queue:
    if user_id not in _user_queues:
        _user_queues[user_id] = asyncio.Queue(maxsize=100)
    return _user_queues[user_id]


async def publish_event(user_id: str, event_type: str, data: dict):
    """Publish an event to a user's SSE stream."""
    queue = get_user_queue(user_id)
    try:
        queue.put_nowait({"event": event_type, "data": data})
    except asyncio.QueueFull:
        logger.warning("SSE queue full for user %s, dropping event", user_id)


@router.get("/activity/stream")
async def agent_activity_stream(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """SSE stream of agent activity for the authenticated user."""
    user_id = str(current_user.id)
    queue = get_user_queue(user_id)

    async def event_generator():
        # Send initial heartbeat
        yield {"event": "connected", "data": json.dumps({"user_id": user_id})}

        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], default=str),
                }
            except asyncio.TimeoutError:
                # Send keepalive ping every 30s
                yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(event_generator())
