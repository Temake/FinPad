"""Gamification routes - Phase 7 implementation."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/badges")
async def list_badges():
    """List all available badges."""
    # TODO: Phase 7 implementation
    return {"message": "Not yet implemented"}


@router.get("/badges/mine")
async def my_badges():
    """Get badges earned by current user."""
    # TODO: Phase 7 implementation
    return {"message": "Not yet implemented"}


@router.get("/stats")
async def user_stats():
    """Get user engagement stats (streaks, totals, level)."""
    # TODO: Phase 7 implementation
    return {"message": "Not yet implemented"}
