"""Prediction API endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.user import User
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionResolveRequest,
    PredictionResponse,
)
from app.services.prediction_engine import PredictionEngine
from app.services.graphiti_client import get_graphiti_client

router = APIRouter(tags=["Predictions"])


@router.get("/active", response_model=PredictionListResponse)
async def get_active_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active predictions for the current user."""
    stmt = (
        select(PredictedPattern)
        .where(
            PredictedPattern.user_id == current_user.id,
            PredictedPattern.status == PredictionStatus.ACTIVE,
        )
        .order_by(PredictedPattern.confidence.desc())
    )
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    return PredictionListResponse(
        predictions=[PredictionResponse.model_validate(p) for p in predictions],
        total=len(predictions),
    )


@router.get("/history", response_model=PredictionListResponse)
async def get_prediction_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get prediction history for the current user."""
    count_stmt = (
        select(func.count())
        .select_from(PredictedPattern)
        .where(PredictedPattern.user_id == current_user.id)
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(PredictedPattern)
        .where(PredictedPattern.user_id == current_user.id)
        .order_by(PredictedPattern.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    return PredictionListResponse(
        predictions=[PredictionResponse.model_validate(p) for p in predictions],
        total=total,
    )


@router.post("/{prediction_id}/resolve", response_model=PredictionResponse)
async def resolve_prediction(
    prediction_id: UUID,
    body: PredictionResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a prediction as confirmed or avoided."""
    stmt = select(PredictedPattern).where(
        PredictedPattern.id == prediction_id,
        PredictedPattern.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    prediction = result.scalar_one_or_none()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    prediction.status = body.status
    prediction.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prediction)

    return PredictionResponse.model_validate(prediction)


@router.post("/run")
async def run_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger prediction engine for the current user."""
    graphiti = get_graphiti_client()
    engine = PredictionEngine(db, graphiti_client=graphiti)

    expired = await engine.expire_old_predictions(str(current_user.id))
    predictions = await engine.predict(str(current_user.id))
    await db.commit()

    return {
        "predictions": predictions,
        "expired_count": expired,
    }
