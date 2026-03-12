"""Tests for expense endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_expenses_unauthorized():
    """Test that /expenses without token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/expenses/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_summary_unauthorized():
    """Test that /expenses/summary without token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/expenses/summary")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_categories_unauthorized():
    """Test that /expenses/categories without token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/expenses/categories")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_expense_unauthorized():
    """Test that POST /expenses without token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/expenses/",
            json={"amount": 1000, "description": "Test expense"}
        )

    assert response.status_code == 401
