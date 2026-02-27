"""Financial education routes - Phase 7 implementation."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/tips")
async def get_daily_tip():
    """Get today's financial micro-tip."""
    # TODO: Phase 7 implementation
    return {"message": "Not yet implemented"}


@router.get("/tips/history")
async def get_tip_history():
    """Get previously delivered tips."""
    # TODO: Phase 7 implementation
    return {"message": "Not yet implemented"}
