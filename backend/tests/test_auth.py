"""Tests for authentication endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_request_otp():
    """Test that OTP request returns success (with debug OTP in dev mode)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone": "2348012345678"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "phone" in data
    assert data["phone"] == "2348012345678"


@pytest.mark.asyncio
async def test_verify_otp_invalid():
    """Test that invalid OTP returns 400."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "2348012345678", "otp": "000000"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired OTP"


@pytest.mark.asyncio
async def test_refresh_invalid_token():
    """Test that invalid refresh token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized():
    """Test that /me without token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
