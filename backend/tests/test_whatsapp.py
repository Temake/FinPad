"""Tests for WhatsApp integration."""

import pytest
from fastapi.testclient import TestClient

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


def test_whatsapp_webhook_new_user_flow():
    """Test new user registration starts confirmation flow."""
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "2348012345678@s.whatsapp.net"},
            "message": {"conversation": "Hi"},
        },
    }
    response = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_confirmation"
    assert data["phone"] == "2348012345678"
