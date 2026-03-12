"""Tests for gamification and education features."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --- Gamification Tests ---

def test_list_badges():
    """Test listing all available badges - public endpoint."""
    response = client.get("/api/v1/gamification/badges")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_my_badges_unauthorized():
    """Test getting user badges without auth."""
    response = client.get("/api/v1/gamification/badges/mine")
    assert response.status_code == 401


def test_user_stats_unauthorized():
    """Test getting user stats without auth."""
    response = client.get("/api/v1/gamification/stats")
    assert response.status_code == 401


def test_leaderboard_unauthorized():
    """Test getting leaderboard without auth."""
    response = client.get("/api/v1/gamification/leaderboard")
    assert response.status_code == 401


# --- Education Tests ---

def test_tip_categories():
    """Test getting tip categories."""
    response = client.get("/api/v1/education/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) == 5  # 5 categories defined
