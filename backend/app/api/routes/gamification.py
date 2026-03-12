"""Gamification routes - badges, streaks, stats, and leaderboard."""

from fastapi import APIRouter

from app.api.deps import DbSession, CurrentUser
from app.schemas.gamification import (
    BadgeResponse,
    UserBadgeResponse,
    UserStatsResponse,
    LeaderboardResponse,
    LeaderboardEntry,
)
from app.services.gamification_service import (
    get_all_badges,
    get_user_badges,
    get_user_stats_with_badges,
    get_leaderboard,
    check_and_award_badges,
)

router = APIRouter()


@router.get("/badges", response_model=list[BadgeResponse])
async def list_badges(db: DbSession):
    """List all available badges."""
    badges = await get_all_badges(db)
    return badges


@router.get("/badges/mine", response_model=list[UserBadgeResponse])
async def my_badges(db: DbSession, user: CurrentUser):
    """Get badges earned by current user."""
    user_badges = await get_user_badges(db, user.id)
    return user_badges


@router.get("/stats", response_model=UserStatsResponse)
async def user_stats(db: DbSession, user: CurrentUser):
    """Get user engagement stats (streaks, totals, level)."""
    stats = await get_user_stats_with_badges(db, user.id)
    return stats


@router.post("/badges/check", response_model=list[UserBadgeResponse])
async def check_badges(db: DbSession, user: CurrentUser):
    """
    Check and award any badges the user has earned.
    
    Returns newly awarded badges.
    """
    new_badges = await check_and_award_badges(db, user.id)
    return new_badges


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(db: DbSession, user: CurrentUser, limit: int = 10):
    """
    Get anonymized leaderboard.
    
    Shows top users by longest streak.
    """
    result = await get_leaderboard(db, limit=min(limit, 50), current_user_id=user.id)
    return LeaderboardResponse(
        entries=[LeaderboardEntry(**e) for e in result["entries"]],
        user_rank=result["user_rank"],
    )
