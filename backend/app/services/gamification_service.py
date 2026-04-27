"""Gamification service - streaks, badges, levels, and leaderboard."""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gamification import Badge, UserBadge, UserStats
from app.models.expense import Expense
from app.models.user import User


# Level progression thresholds
LEVELS = [
    ("Beginner Saver", 0),
    ("Consistent Tracker", 10),       # 10 expenses
    ("Budget Aware", 30),             # 30 expenses
    ("Money Manager", 75),            # 75 expenses
    ("Finance Pro", 150),             # 150 expenses
    ("Wealth Master", 300),           # 300 expenses
]


def get_level_for_expenses(total_expenses: int) -> tuple[str, str | None, float]:
    """
    Get level name, next level, and progress based on total expenses.
    
    Returns:
        Tuple of (current_level, next_level, progress_to_next)
    """
    current_level = LEVELS[0][0]
    next_level = None
    progress = 0.0
    
    for i, (level_name, threshold) in enumerate(LEVELS):
        if total_expenses >= threshold:
            current_level = level_name
            if i + 1 < len(LEVELS):
                next_level = LEVELS[i + 1][0]
                next_threshold = LEVELS[i + 1][1]
                progress = (total_expenses - threshold) / (next_threshold - threshold)
                progress = min(progress, 1.0)
    
    return current_level, next_level, progress


async def get_or_create_user_stats(db: AsyncSession, user_id: uuid.UUID) -> UserStats:
    """Get user stats, creating if they don't exist."""
    result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    stats = result.scalar_one_or_none()
    
    if not stats:
        stats = UserStats(user_id=user_id)
        db.add(stats)
        await db.flush()
        await db.refresh(stats)
    
    return stats


async def get_user_stats_with_badges(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """Get user stats with badge count and level info."""
    stats = await get_or_create_user_stats(db, user_id)
    
    # Count badges
    badge_count_result = await db.execute(
        select(func.count(UserBadge.id)).where(UserBadge.user_id == user_id)
    )
    badges_earned = badge_count_result.scalar() or 0
    
    # Calculate level info
    level, next_level, progress = get_level_for_expenses(stats.total_expenses_logged)
    
    return {
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "total_expenses_logged": stats.total_expenses_logged,
        "level": level,
        "badges_earned": badges_earned,
        "next_level": next_level,
        "progress_to_next_level": progress,
    }


async def increment_expense_count(
    db: AsyncSession, user_id: uuid.UUID
) -> UserStats:
    """Increment total expenses and check for level up."""
    stats = await get_or_create_user_stats(db, user_id)
    stats.total_expenses_logged += 1
    
    # Update level
    new_level, _, _ = get_level_for_expenses(stats.total_expenses_logged)
    stats.level = new_level
    
    await db.flush()
    await db.refresh(stats)
    return stats


async def update_streak(
    db: AsyncSession, user_id: uuid.UUID, expense_date: date
) -> tuple[UserStats, bool]:
    """
    Update user's streak based on expense logging.
    
    Returns:
        Tuple of (stats, is_new_streak_milestone)
    """
    stats = await get_or_create_user_stats(db, user_id)
    
    # Get user's most recent expense date before this one
    result = await db.execute(
        select(func.max(Expense.expense_date))
        .where(
            and_(
                Expense.user_id == user_id,
                Expense.expense_date < expense_date,
                Expense.is_deleted == False,
            )
        )
    )
    last_expense_date = result.scalar()
    
    is_milestone = False
    old_streak = stats.current_streak
    
    if last_expense_date is None:
        # First expense ever
        stats.current_streak = 1
    elif expense_date - last_expense_date == timedelta(days=1):
        # Consecutive day - increase streak
        stats.current_streak += 1
    elif expense_date == last_expense_date:
        # Same day - no change to streak
        pass
    else:
        # Streak broken - reset to 1
        stats.current_streak = 1
    
    # Update longest streak
    if stats.current_streak > stats.longest_streak:
        stats.longest_streak = stats.current_streak
    
    # Check for milestone (3, 7, 14, 21, 30, 60, 90, etc.)
    milestones = {3, 7, 14, 21, 30, 60, 90, 180, 365}
    if stats.current_streak in milestones and stats.current_streak != old_streak:
        is_milestone = True
    
    await db.flush()
    await db.refresh(stats)
    return stats, is_milestone


async def get_all_badges(db: AsyncSession) -> list[Badge]:
    """Get all available badges."""
    result = await db.execute(select(Badge).order_by(Badge.id))
    return list(result.scalars().all())


async def get_user_badges(
    db: AsyncSession, user_id: uuid.UUID
) -> list[UserBadge]:
    """Get all badges earned by a user."""
    result = await db.execute(
        select(UserBadge)
        .options(selectinload(UserBadge.badge))
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.desc())
    )
    return list(result.scalars().all())


async def has_badge(db: AsyncSession, user_id: uuid.UUID, criteria_type: str) -> bool:
    """Check if user already has a badge by criteria type."""
    result = await db.execute(
        select(UserBadge)
        .join(Badge)
        .where(
            and_(
                UserBadge.user_id == user_id,
                Badge.criteria_type == criteria_type,
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def award_badge(
    db: AsyncSession, user_id: uuid.UUID, criteria_type: str
) -> UserBadge | None:
    """
    Award a badge to user if they don't already have it.
    
    Returns:
        UserBadge if awarded, None if already had or badge doesn't exist
    """
    # Check if user already has this badge
    if await has_badge(db, user_id, criteria_type):
        return None
    
    # Find the badge
    result = await db.execute(
        select(Badge).where(Badge.criteria_type == criteria_type)
    )
    badge = result.scalar_one_or_none()
    
    if not badge:
        return None
    
    # Award badge
    user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
    db.add(user_badge)
    await db.flush()
    await db.refresh(user_badge)
    
    # Load badge relationship
    result = await db.execute(
        select(UserBadge)
        .options(selectinload(UserBadge.badge))
        .where(UserBadge.id == user_badge.id)
    )
    return result.scalar_one()


async def check_and_award_badges(
    db: AsyncSession, user_id: uuid.UUID
) -> list[UserBadge]:
    """
    Check all badge criteria and award any earned badges.
    
    Returns:
        List of newly awarded badges
    """
    stats = await get_or_create_user_stats(db, user_id)
    awarded = []
    
    # First expense badge
    if stats.total_expenses_logged >= 1:
        badge = await award_badge(db, user_id, "first_expense")
        if badge:
            awarded.append(badge)
    
    # Streak badges
    streak_badges = [
        (3, "streak_3"),
        (7, "streak_7"),
        (14, "streak_14"),
        (30, "streak_30"),
        (60, "streak_60"),
        (90, "streak_90"),
    ]
    for streak_days, criteria in streak_badges:
        if stats.longest_streak >= streak_days:
            badge = await award_badge(db, user_id, criteria)
            if badge:
                awarded.append(badge)
    
    # Expense count badges
    count_badges = [
        (10, "expenses_10"),
        (50, "expenses_50"),
        (100, "expenses_100"),
        (500, "expenses_500"),
    ]
    for count, criteria in count_badges:
        if stats.total_expenses_logged >= count:
            badge = await award_badge(db, user_id, criteria)
            if badge:
                awarded.append(badge)
    
    return awarded


async def get_leaderboard(
    db: AsyncSession,
    limit: int = 10,
    current_user_id: uuid.UUID | None = None,
) -> dict:
    """
    Get anonymized leaderboard.
    
    Returns:
        Dict with entries and current user's rank
    """
    # Get top users by streak
    result = await db.execute(
        select(UserStats)
        .order_by(UserStats.longest_streak.desc(), UserStats.total_expenses_logged.desc())
        .limit(limit)
    )
    top_stats = list(result.scalars().all())
    
    entries = []
    user_rank = None
    
    for i, stat in enumerate(top_stats, 1):
        # Get badge count
        badge_result = await db.execute(
            select(func.count(UserBadge.id)).where(UserBadge.user_id == stat.user_id)
        )
        badge_count = badge_result.scalar() or 0
        
        # Anonymize
        display_name = f"User #{str(stat.user_id)[:4].upper()}"
        
        entries.append({
            "rank": i,
            "display_name": display_name,
            "streak": stat.longest_streak,
            "badges_count": badge_count,
            "level": stat.level,
        })
        
        if current_user_id and stat.user_id == current_user_id:
            user_rank = i
    
    return {"entries": entries, "user_rank": user_rank}
