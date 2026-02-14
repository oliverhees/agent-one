"""Pydantic schemas for prediction endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response schema for a single prediction."""

    id: str
    user_id: str
    pattern_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    predicted_for: datetime
    time_horizon: str
    trigger_factors: dict[str, Any]
    graphiti_context: dict[str, Any]
    status: str
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    """Response schema for a list of predictions."""

    predictions: list[PredictionResponse]
    total: int


class PredictionResolveRequest(BaseModel):
    """Request to resolve a prediction."""

    status: Literal["confirmed", "avoided"]
