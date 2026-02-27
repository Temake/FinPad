"""User profile routes - view and update profile."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserId, DbSession
from app.schemas.user import UserProfile, UserProfileUpdate
from app.services.user_service import get_user_by_id, update_user_profile

router = APIRouter()


@router.get("/", response_model=UserProfile)
async def get_profile(user_id: CurrentUserId, db: DbSession):
    """Get current user's profile (same as /auth/me)."""
    user = await get_user_by_id(db, uuid.UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    streak = 0
    level = "Beginner Saver"
    if user.user_stats:
        streak = user.user_stats.current_streak
        level = user.user_stats.level

    return UserProfile(
        id=user.id,
        phone=user.phone,
        display_name=user.display_name,
        currency=user.currency,
        notification_enabled=user.notification_enabled,
        daily_reminder_time=user.daily_reminder_time,
        whatsapp_linked=user.whatsapp_linked,
        current_streak=streak,
        level=level,
    )


@router.put("/", response_model=UserProfile)
async def update_profile(
    updates: UserProfileUpdate,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Update current user's profile."""
    update_data = updates.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    user = await update_user_profile(db, uuid.UUID(user_id), **update_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    streak = 0
    level = "Beginner Saver"
    if user.user_stats:
        streak = user.user_stats.current_streak
        level = user.user_stats.level

    return UserProfile(
        id=user.id,
        phone=user.phone,
        display_name=user.display_name,
        currency=user.currency,
        notification_enabled=user.notification_enabled,
        daily_reminder_time=user.daily_reminder_time,
        whatsapp_linked=user.whatsapp_linked,
        current_streak=streak,
        level=level,
    )
