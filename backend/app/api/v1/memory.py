"""Memory API endpoints for knowledge graph status, export, and DSGVO compliance."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.memory import (
    MemorySettingsUpdate,
    MemoryStatusResponse,
    PatternLogResponse,
)
from app.services.graphiti_client import get_graphiti_client
from app.services.memory import MemoryService

router = APIRouter(tags=["Memory"])


@router.get(
    "/status",
    response_model=MemoryStatusResponse,
    summary="Get memory system status",
    description="Returns current memory/knowledge graph status including entity counts and last analysis timestamp.",
)
async def get_memory_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the memory system status for the authenticated user."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    status_data = await service.get_status(str(current_user.id))
    return MemoryStatusResponse(**status_data)


@router.get(
    "/export",
    summary="Export all memory data (DSGVO Art. 15)",
    description="Export all stored memory data for the authenticated user. "
    "Implements DSGVO Art. 15 (Right of Access).",
)
async def export_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all memory data for DSGVO Art. 15 compliance."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    export = await service.export_user_data(str(current_user.id))

    pattern_logs = [
        PatternLogResponse.model_validate(log).model_dump(mode="json")
        for log in export["pattern_logs"]
    ]

    return {
        "entities": export["entities"],
        "relations": export["relations"],
        "pattern_logs": pattern_logs,
        "exported_at": export["exported_at"].isoformat(),
    }


@router.delete(
    "",
    summary="Delete all memory data (DSGVO Art. 17)",
    description="Delete all stored memory data for the authenticated user. "
    "Implements DSGVO Art. 17 (Right to Erasure).",
)
async def delete_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all memory data for DSGVO Art. 17 compliance."""
    graphiti = get_graphiti_client()
    service = MemoryService(db, graphiti)
    deleted = await service.delete_user_data(str(current_user.id))
    await db.commit()
    return {"deleted": deleted}


@router.put(
    "/settings",
    summary="Update memory settings",
    description="Enable or disable the memory/learning system for the authenticated user.",
)
async def update_memory_settings(
    data: MemorySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update memory settings (enable/disable learning)."""
    from app.services.settings import SettingsService

    settings_service = SettingsService(db)
    user_settings = await settings_service._get_or_create_settings(current_user.id)
    current = user_settings.settings or {}
    current["memory_enabled"] = data.enabled
    user_settings.settings = current
    await db.flush()
    await db.commit()
    return {"enabled": data.enabled}
