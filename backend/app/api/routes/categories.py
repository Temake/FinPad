"""Category routes - Phase 3 implementation."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_categories():
    """List all categories (default + user custom)."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.post("/")
async def create_category():
    """Create a custom category."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}
