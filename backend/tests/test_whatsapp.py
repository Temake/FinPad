"""Tests for WhatsApp integration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.whatsapp_service import WhatsAppService, settings

client = TestClient(app)


def test_whatsapp_webhook_verify():
    """Test webhook verification endpoint."""
    response = client.get("/api/v1/whatsapp/webhook")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "finpad-whatsapp"


def test_whatsapp_webhook_non_message_event():
    """Test webhook ignores non-message events."""
    payload = {"event": "connection.update", "data": {}}
    response = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert data["event"] == "connection.update"


def test_whatsapp_webhook_no_phone():
    """Test webhook handles missing phone gracefully."""
    payload = {
        "event": "messages.upsert",
        "data": {"message": {"conversation": "Hello"}},
    }
    response = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"


def test_whatsapp_service_uses_global_key_when_set(monkeypatch: pytest.MonkeyPatch):
    """Use global Evolution API key when configured."""
    monkeypatch.setattr(settings, "EVOLUTION_API_GLOBAL_KEY", "global-key")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "instance-key")

    service = WhatsAppService()

    assert service.headers["apikey"] == "global-key"


def test_whatsapp_service_falls_back_to_instance_key(monkeypatch: pytest.MonkeyPatch):
    """Fallback to instance API key when global key is not configured."""
    monkeypatch.setattr(settings, "EVOLUTION_API_GLOBAL_KEY", "")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "instance-key")

    service = WhatsAppService()

    assert service.headers["apikey"] == "instance-key"


def test_whatsapp_service_raises_when_no_keys(monkeypatch: pytest.MonkeyPatch):
    """Fail fast when no Evolution API key is configured."""
    monkeypatch.setattr(settings, "EVOLUTION_API_GLOBAL_KEY", "")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "")

    with pytest.raises(ValueError, match="Evolution API key is not configured"):
        WhatsAppService()
