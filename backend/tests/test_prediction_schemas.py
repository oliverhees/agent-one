"""Tests for prediction Pydantic schemas."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas.prediction import (
    PredictionResponse,
    PredictionListResponse,
    PredictionResolveRequest,
)


class TestPredictionSchemas:
    def test_prediction_response_serialization(self):
        data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "pattern_type": "energy_crash",
            "confidence": 0.78,
            "predicted_for": datetime.now(timezone.utc) + timedelta(hours=24),
            "time_horizon": "24h",
            "trigger_factors": {"energy_trend": "declining"},
            "graphiti_context": {},
            "status": "active",
            "resolved_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        resp = PredictionResponse(**data)
        assert resp.pattern_type == "energy_crash"
        assert resp.confidence == 0.78
        assert resp.status == "active"

    def test_prediction_list_response(self):
        predictions = []
        for i in range(3):
            predictions.append({
                "id": str(uuid4()),
                "user_id": str(uuid4()),
                "pattern_type": "procrastination",
                "confidence": 0.6 + i * 0.1,
                "predicted_for": datetime.now(timezone.utc),
                "time_horizon": "3d",
                "trigger_factors": {},
                "graphiti_context": {},
                "status": "active",
                "resolved_at": None,
                "created_at": datetime.now(timezone.utc),
            })

        resp = PredictionListResponse(
            predictions=[PredictionResponse(**p) for p in predictions],
            total=3,
        )
        assert resp.total == 3
        assert len(resp.predictions) == 3

    def test_prediction_resolve_request_valid(self):
        req = PredictionResolveRequest(status="confirmed")
        assert req.status == "confirmed"

    def test_prediction_resolve_request_avoided(self):
        req = PredictionResolveRequest(status="avoided")
        assert req.status == "avoided"

    def test_prediction_resolve_request_invalid_status(self):
        with pytest.raises(Exception):
            PredictionResolveRequest(status="active")
