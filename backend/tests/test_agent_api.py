"""Tests for Agent API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_agent_routes_registered(client):
    """Agent routes should be registered in the API."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/agents/trust" in paths
    assert "/api/v1/agents/email/config" in paths
    assert "/api/v1/agents/approvals/pending" in paths


@pytest.mark.asyncio
async def test_get_trust_scores_unauthenticated(client):
    """Unauthenticated requests should return 401."""
    response = await client.get("/api/v1/agents/trust")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_trust_scores_authenticated(authenticated_client):
    """Authenticated requests should return trust scores."""
    response = await authenticated_client.get("/api/v1/agents/trust")
    assert response.status_code == 200
    data = response.json()
    assert "scores" in data


@pytest.mark.asyncio
async def test_get_pending_approvals(authenticated_client):
    """Get pending approval requests."""
    response = await authenticated_client.get("/api/v1/agents/approvals/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_set_trust_level(authenticated_client):
    """Set trust level for an agent type."""
    response = await authenticated_client.put(
        "/api/v1/agents/trust",
        json={"agent_type": "email", "trust_level": 2},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_save_email_config(authenticated_client):
    """Save email configuration."""
    response = await authenticated_client.post(
        "/api/v1/agents/email/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "test123",
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "imap_user": "test@gmail.com",
            "imap_password": "test123",
        },
    )
    assert response.status_code == 200
