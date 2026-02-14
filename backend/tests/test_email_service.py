"""Tests for EmailService (SMTP/IMAP)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.email import EmailService


@pytest.mark.asyncio
async def test_send_email_success():
    service = EmailService(None)
    with patch("app.services.email.aiosmtplib") as mock_smtp:
        mock_client = AsyncMock()
        mock_smtp.SMTP.return_value = mock_client
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.login = AsyncMock()
        mock_client.send_message = AsyncMock()

        result = await service.send_email(
            smtp_host="smtp.test.com", smtp_port=587,
            smtp_user="test@test.com", smtp_password="pass",
            to="recipient@test.com", subject="Test", body="Hello",
        )
        assert result["success"] is True


@pytest.mark.asyncio
async def test_send_email_timeout():
    service = EmailService(None)
    with patch("app.services.email.aiosmtplib") as mock_smtp:
        mock_smtp.SMTP.side_effect = TimeoutError("Connection timed out")
        result = await service.send_email(
            smtp_host="smtp.test.com", smtp_port=587,
            smtp_user="test@test.com", smtp_password="pass",
            to="recipient@test.com", subject="Test", body="Hello",
        )
        assert result["success"] is False
        assert "error" in result
