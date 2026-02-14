"""Wellbeing/Guardian Angel API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.wellbeing import (
    InterventionAction,
    InterventionResponse,
    WellbeingHistoryResponse,
    WellbeingScoreResponse,
)
from app.services.wellbeing import WellbeingService

router = APIRouter(tags=["Wellbeing"])


@router.get(
    "/score",
    response_model=WellbeingScoreResponse,
    summary="Get current wellbeing score",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_wellbeing_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest wellbeing score. Calculates a new one if none exists or if stale."""
    service = WellbeingService(db)
    latest = await service.get_latest_score(str(current_user.id))
    if not latest:
        latest = await service.calculate_and_store(str(current_user.id))
        await db.commit()
    return WellbeingScoreResponse(**latest)


@router.get(
    "/history",
    response_model=WellbeingHistoryResponse,
    summary="Get wellbeing score history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_wellbeing_history(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get wellbeing score history for the last N days."""
    service = WellbeingService(db)
    history = await service.get_score_history(str(current_user.id), days=days)
    return WellbeingHistoryResponse(
        scores=[WellbeingScoreResponse(**s) for s in history["scores"]],
        trend=history["trend"],
        average_score=history["average_score"],
        days=history["days"],
    )


@router.get(
    "/interventions",
    response_model=list[InterventionResponse],
    summary="Get active interventions",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_interventions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending interventions for the current user."""
    service = WellbeingService(db)
    interventions = await service.get_active_interventions(str(current_user.id))
    return [InterventionResponse(**i) for i in interventions]


@router.put(
    "/interventions/{intervention_id}",
    summary="Dismiss or act on an intervention",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_intervention(
    intervention_id: str,
    data: InterventionAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update intervention status: dismiss or act."""
    service = WellbeingService(db)
    status_map = {"dismiss": "dismissed", "act": "acted"}
    new_status = status_map[data.action]
    success = await service.update_intervention_status(
        intervention_id, str(current_user.id), new_status
    )
    if not success:
        raise HTTPException(status_code=404, detail="Intervention not found")
    await db.commit()
    return {"status": new_status}
