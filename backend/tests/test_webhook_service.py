"""Tests for WebhookService."""
import pytest
import hashlib
import hmac
import json
from app.services.webhook import WebhookService


class TestWebhookService:
    def test_generate_secret(self):
        secret = WebhookService.generate_secret()
        assert len(secret) == 64  # 32 bytes hex

    def test_verify_signature_valid(self):
        secret = "test-secret"
        payload = json.dumps({"event": "test"}).encode()
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected}"
        assert WebhookService.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        assert WebhookService.verify_signature(b"data", "sha256=bad", "secret") is False
