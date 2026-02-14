"""Tests for prediction API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestPredictionAPI:
    @pytest.mark.asyncio
    async def test_get_active_predictions_empty(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test getting active predictions when there are none."""
        response = await authenticated_client.get("/api/v1/predictions/active")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total" in data
        assert data["total"] == 0
        assert data["predictions"] == []

    @pytest.mark.asyncio
    async def test_get_prediction_history_empty(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test getting prediction history when empty."""
        response = await authenticated_client.get("/api/v1/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_prediction_history_pagination(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test pagination parameters are accepted."""
        response = await authenticated_client.get(
            "/api/v1/predictions/history?limit=2&offset=0"
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_prediction(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test that resolving non-existent prediction returns 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(
            f"/api/v1/predictions/{fake_id}/resolve",
            json={"status": "confirmed"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_resolve_invalid_status(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test that invalid status values are rejected."""
        fake_id = str(uuid4())

        response = await authenticated_client.post(
            f"/api/v1/predictions/{fake_id}/resolve",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_run_predictions_manually(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """Test manually triggering prediction engine."""
        response = await authenticated_client.post("/api/v1/predictions/run")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "expired_count" in data
        assert isinstance(data["predictions"], list)
        assert isinstance(data["expired_count"], int)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that endpoints require authentication."""
        endpoints = [
            ("/api/v1/predictions/active", "GET"),
            ("/api/v1/predictions/history", "GET"),
            ("/api/v1/predictions/run", "POST"),
        ]

        for path, method in endpoints:
            if method == "GET":
                response = await client.get(path)
            else:
                response = await client.post(path)
            assert response.status_code == 403  # Unauthorized


class TestPredictionRouterRegistered:
    """Test that prediction router is correctly registered."""

    def test_prediction_prefix_in_v1_router(self):
        """Test that /predictions prefix is registered in main v1 router."""
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/predictions" in p for p in paths)


class TestPredictionEndpointsExist:
    """Test that all expected endpoints exist on prediction router."""

    def test_router_has_active_endpoint(self):
        from app.api.v1 import prediction
        paths = [r.path for r in prediction.router.routes]
        assert "/active" in paths

    def test_router_has_history_endpoint(self):
        from app.api.v1 import prediction
        paths = [r.path for r in prediction.router.routes]
        assert "/history" in paths

    def test_router_has_resolve_endpoint(self):
        from app.api.v1 import prediction
        paths = [r.path for r in prediction.router.routes]
        assert any("{prediction_id}" in p and "resolve" in p for p in paths)

    def test_router_has_run_endpoint(self):
        from app.api.v1 import prediction
        paths = [r.path for r in prediction.router.routes]
        assert "/run" in paths

    def test_active_is_get(self):
        from app.api.v1 import prediction
        for route in prediction.router.routes:
            if hasattr(route, "path") and route.path == "/active":
                assert "GET" in route.methods

    def test_history_is_get(self):
        from app.api.v1 import prediction
        for route in prediction.router.routes:
            if hasattr(route, "path") and route.path == "/history":
                assert "GET" in route.methods

    def test_resolve_is_post(self):
        from app.api.v1 import prediction
        for route in prediction.router.routes:
            if hasattr(route, "path") and "resolve" in route.path:
                assert "POST" in route.methods

    def test_run_is_post(self):
        from app.api.v1 import prediction
        for route in prediction.router.routes:
            if hasattr(route, "path") and route.path == "/run":
                assert "POST" in route.methods
