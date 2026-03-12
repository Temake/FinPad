"""Financial education routes - tips and learning content."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.education import (
    FinancialTipResponse,
    DailyTipResponse,
)
from app.services.education_service import (
    get_daily_tip,
    get_all_tips,
    get_tips_by_category,
    get_tip_count,
)

router = APIRouter()


@router.get("/tips/daily", response_model=DailyTipResponse | None)
async def daily_tip(db: DbSession):
    """
    Get today's financial micro-tip.
    
    Returns the same tip for all users on the same day.
    """
    result = await get_daily_tip(db)
    if not result:
        return None
    return DailyTipResponse(
        tip=result["tip"],
        tip_number=result["tip_number"],
        category_emoji=result["category_emoji"],
    )


@router.get("/tips", response_model=list[FinancialTipResponse])
async def list_tips(
    db: DbSession,
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get financial tips with optional filtering.
    
    Categories: savings, budgeting, investing, debt_management, general
    """
    if category:
        tips = await get_tips_by_category(db, category, limit)
    else:
        tips = await get_all_tips(db, limit, offset)
    return tips


@router.get("/tips/count")
async def tip_count(db: DbSession):
    """Get total number of available tips."""
    count = await get_tip_count(db)
    return {"count": count}


@router.get("/categories")
async def tip_categories():
    """Get available tip categories with descriptions."""
    return {
        "categories": [
            {"name": "savings", "emoji": "💰", "description": "Tips on building savings"},
            {"name": "budgeting", "emoji": "📊", "description": "Budgeting strategies"},
            {"name": "investing", "emoji": "📈", "description": "Investment basics"},
            {"name": "debt_management", "emoji": "🏦", "description": "Managing debt wisely"},
            {"name": "general", "emoji": "💡", "description": "General money tips"},
        ]
    }
