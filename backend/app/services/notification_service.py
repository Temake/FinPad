"""Notification service - scheduled reminders and summaries via WhatsApp."""

import logging
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.expense_service import get_expense_summary
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


async def get_users_for_daily_reminder(
    db: AsyncSession, 
    current_hour: int,
    current_minute: int = 0,
) -> list[User]:
    """
    Get users who should receive daily reminder at current time.
    
    Args:
        db: Database session
        current_hour: Current hour (0-23)
        current_minute: Current minute (0-59), used for 15-min window
        
    Returns:
        List of users to notify
    """
    # Format as HH:MM
    target_time = f"{current_hour:02d}:00"
    
    query = select(User).where(
        and_(
            User.notification_enabled == True,
            User.whatsapp_linked == True,
            User.is_active == True,
            User.daily_reminder_time == target_time,
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def send_daily_reminders(db: AsyncSession) -> dict:
    """
    Send daily reminders to users at their preferred time.
    Should be called by a scheduler every hour.
    
    Returns:
        Dict with sent count and any errors
    """
    now = datetime.now(timezone.utc)
    # Adjust for Nigerian time (WAT = UTC+1)
    nigeria_hour = (now.hour + 1) % 24
    
    users = await get_users_for_daily_reminder(db, nigeria_hour)
    
    whatsapp = WhatsAppService()
    sent = 0
    errors = []
    
    for user in users:
        try:
            success = await whatsapp.send_daily_reminder(user.phone)
            if success:
                sent += 1
                logger.info(f"Sent daily reminder to {user.phone}")
            else:
                errors.append(f"Failed to send to {user.phone}")
        except Exception as e:
            logger.error(f"Error sending reminder to {user.phone}: {e}")
            errors.append(str(e))
    
    return {"sent": sent, "total_users": len(users), "errors": errors}


async def send_weekly_summaries(db: AsyncSession) -> dict:
    """
    Send weekly summaries to all active WhatsApp users.
    Should be called weekly (e.g., every Sunday evening).
    
    Returns:
        Dict with sent count and any errors
    """
    query = select(User).where(
        and_(
            User.notification_enabled == True,
            User.whatsapp_linked == True,
            User.is_active == True,
        )
    )
    result = await db.execute(query)
    users = list(result.scalars().all())
    
    whatsapp = WhatsAppService()
    sent = 0
    errors = []
    
    for user in users:
        try:
            # Get this week's summary
            summary = await get_expense_summary(db, user.id, "weekly")
            
            # Find top category
            top_category = None
            if summary["by_category"]:
                top_category = max(summary["by_category"], key=summary["by_category"].get)
            
            success = await whatsapp.send_weekly_summary(
                user.phone,
                summary["total"],
                summary["count"],
                top_category,
            )
            
            if success:
                sent += 1
                logger.info(f"Sent weekly summary to {user.phone}")
            else:
                errors.append(f"Failed to send to {user.phone}")
                
        except Exception as e:
            logger.error(f"Error sending weekly summary to {user.phone}: {e}")
            errors.append(str(e))
    
    return {"sent": sent, "total_users": len(users), "errors": errors}


async def check_and_send_streak_notification(
    db: AsyncSession,
    user: User,
    current_streak: int,
) -> bool:
    """
    Send streak achievement notification if milestone reached.
    
    Args:
        db: Database session
        user: User to notify
        current_streak: User's current streak count
        
    Returns:
        True if notification was sent
    """
    # Milestone days
    milestones = {3, 7, 14, 21, 30, 60, 90, 180, 365}
    
    if current_streak not in milestones:
        return False
    
    if not user.whatsapp_linked or not user.notification_enabled:
        return False
    
    whatsapp = WhatsAppService()
    return await whatsapp.send_streak_achievement(user.phone, current_streak)
