"""Tests for WhatsApp integration."""

import pytest
from fastapi.testclient import TestClient

from app.api.routes import whatsapp as whatsapp_route
from app.main import app

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


@pytest.mark.parametrize(
    "message_text",
    ["YES", " yes ", "Yes!", "yes✅", "OK", "okay please"],
)
def test_confirmation_canonicalization(message_text: str):
    """Confirmation parser should accept YES variants with punctuation/emoji."""
    assert whatsapp_route._is_confirmation_yes(message_text) is True


def test_whatsapp_webhook_duplicate_message_id():
    """Webhook should ignore duplicate message IDs for replay protection."""
    whatsapp_route._processed_message_ids.clear()

    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"id": "msg-dup-001", "fromMe": False},
            "message": {"conversation": "Hello"},
        },
    }

    first = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert first.status_code == 200
    assert first.json()["status"] == "ignored"
    assert first.json()["reason"] == "no phone or message"

    second = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert second.status_code == 200
    data = second.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "duplicate_event"


def test_whatsapp_webhook_malformed_event_shape():
    """Webhook should reject malformed messages.upsert event shape."""
    payload = {
        "event": "messages.upsert",
        "data": "not-an-object",
    }
    response = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "malformed_event_payload"


def test_whatsapp_webhook_payload_too_large(monkeypatch):
    """Webhook should enforce maximum payload size limit."""
    monkeypatch.setattr(whatsapp_route, "MAX_WEBHOOK_PAYLOAD_BYTES", 64)

    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "2348012345678@s.whatsapp.net", "id": "msg-big-001"},
            "message": {"conversation": "x" * 500},
        },
    }
    response = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "payload_too_large"


def test_whatsapp_webhook_rate_limited(monkeypatch):
    """Webhook should throttle repeated events from same source."""
    whatsapp_route._rate_limit_tracker.clear()
    whatsapp_route._processed_message_ids.clear()
    whatsapp_route._pending_registrations.clear()

    monkeypatch.setattr(whatsapp_route, "RATE_LIMIT_MAX_MESSAGES", 1)
    monkeypatch.setattr(whatsapp_route, "RATE_LIMIT_WINDOW_SECONDS", 3600)

    first_payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "2348012345678@s.whatsapp.net", "id": "msg-rate-001", "fromMe": False},
            "message": {"conversation": "Hi"},
        },
    }
    second_payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "2348012345678@s.whatsapp.net", "id": "msg-rate-002", "fromMe": False},
            "message": {"conversation": "Hi again"},
        },
    }

    first = client.post("/api/v1/whatsapp/webhook", json=first_payload)
    assert first.status_code == 200

    second = client.post("/api/v1/whatsapp/webhook", json=second_payload)
    assert second.status_code == 200
    data = second.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "rate_limited"
