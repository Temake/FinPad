"""Pydantic schemas for gamification (badges, streaks, stats)."""

from datetime import datetime
from pydantic import BaseModel


class BadgeBase(BaseModel):
    """Base badge schema."""
    name: str
    description: str
    icon: str | None = None
    criteria_type: str


class BadgeResponse(BadgeBase):
    """Badge response schema."""
    id: int

    model_config = {"from_attributes": True}


class UserBadgeResponse(BaseModel):
    """User's earned badge with timestamp."""
    id: int
    badge: BadgeResponse
    earned_at: datetime

    model_config = {"from_attributes": True}


class UserStatsResponse(BaseModel):
    """User engagement statistics."""
    current_streak: int
    longest_streak: int
    total_expenses_logged: int
    level: str
    badges_earned: int = 0
    next_level: str | None = None
    progress_to_next_level: float = 0.0  # 0.0 - 1.0

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    """Anonymized leaderboard entry."""
    rank: int
    display_name: str  # Anonymized: "User #1234"
    streak: int
    badges_count: int
    level: str


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    entries: list[LeaderboardEntry]
    user_rank: int | None = None  # Current user's rank if in top
