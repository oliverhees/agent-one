"""Tests for wellbeing API router registration and endpoint existence."""

import pytest


class TestWellbeingRouterRegistered:
    def test_wellbeing_prefix_in_v1_router(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/wellbeing" in p for p in paths)


class TestWellbeingEndpointsExist:
    def test_router_has_score_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/score" in paths

    def test_router_has_history_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/history" in paths

    def test_router_has_interventions_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert "/interventions" in paths

    def test_router_has_intervention_action_endpoint(self):
        from app.api.v1.wellbeing import router
        paths = [r.path for r in router.routes]
        assert any("intervention" in p and "{intervention_id}" in p for p in paths)

    def test_score_endpoint_is_get(self):
        from app.api.v1.wellbeing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/score":
                assert "GET" in route.methods

    def test_interventions_action_is_put(self):
        from app.api.v1.wellbeing import router
        for route in router.routes:
            if hasattr(route, "path") and "{intervention_id}" in route.path:
                assert "PUT" in route.methods
