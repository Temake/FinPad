"""Education service - financial tips delivery and management."""

import random
from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.education import FinancialTip


# Category emoji mapping
CATEGORY_EMOJIS = {
    "savings": "💰",
    "budgeting": "📊",
    "investing": "📈",
    "debt_management": "🏦",
    "general": "💡",
}


async def get_random_tip(
    db: AsyncSession, 
    category: str | None = None
) -> FinancialTip | None:
    """
    Get a random financial tip.
    
    Args:
        db: Database session
        category: Optional category filter
        
    Returns:
        Random tip or None if no tips exist
    """
    query = select(FinancialTip).where(FinancialTip.is_active == True)
    
    if category:
        query = query.where(FinancialTip.category == category)
    
    result = await db.execute(query)
    tips = list(result.scalars().all())
    
    if not tips:
        return None
    
    return random.choice(tips)


async def get_daily_tip(db: AsyncSession) -> dict | None:
    """
    Get today's financial tip.
    
    Uses the day of year to select a consistent tip for the day,
    so all users get the same tip on the same day.
    
    Returns:
        Dict with tip, tip_number, and category_emoji
    """
    # Get total tip count
    count_result = await db.execute(
        select(func.count(FinancialTip.id)).where(FinancialTip.is_active == True)
    )
    total_tips = count_result.scalar() or 0
    
    if total_tips == 0:
        return None
    
    # Use day of year to pick tip
    day_of_year = date.today().timetuple().tm_yday
    tip_index = day_of_year % total_tips
    
    # Get tip at that index
    result = await db.execute(
        select(FinancialTip)
        .where(FinancialTip.is_active == True)
        .order_by(FinancialTip.id)
        .offset(tip_index)
        .limit(1)
    )
    tip = result.scalar_one_or_none()
    
    if not tip:
        return None
    
    category_emoji = CATEGORY_EMOJIS.get(tip.category, "💡")
    
    return {
        "tip": tip,
        "tip_number": tip_index + 1,
        "category_emoji": category_emoji,
    }


async def get_tips_by_category(
    db: AsyncSession,
    category: str,
    limit: int = 10,
) -> list[FinancialTip]:
    """Get tips filtered by category."""
    result = await db.execute(
        select(FinancialTip)
        .where(
            FinancialTip.is_active == True,
            FinancialTip.category == category,
        )
        .order_by(FinancialTip.id)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_tips(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[FinancialTip]:
    """Get all active tips with pagination."""
    result = await db.execute(
        select(FinancialTip)
        .where(FinancialTip.is_active == True)
        .order_by(FinancialTip.id)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_tip_count(db: AsyncSession) -> int:
    """Get total number of active tips."""
    result = await db.execute(
        select(func.count(FinancialTip.id)).where(FinancialTip.is_active == True)
    )
    return result.scalar() or 0


def format_tip_for_whatsapp(tip: FinancialTip, tip_number: int) -> str:
    """Format a financial tip for WhatsApp delivery."""
    emoji = CATEGORY_EMOJIS.get(tip.category, "💡")
    icon = tip.icon or emoji
    
    return (
        f"{icon} *Did You Know? (Tip #{tip_number})*\n\n"
        f"*{tip.title}*\n\n"
        f"{tip.content}\n\n"
        f"_Category: {tip.category.replace('_', ' ').title()}_"
    )
