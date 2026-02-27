"""Expense routes - Phase 3 implementation."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_expense():
    """Create a new expense entry."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.get("/")
async def list_expenses():
    """List expenses with filters (date range, category, etc.)."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.get("/summary")
async def expense_summary():
    """Get expense summary (daily/weekly/monthly aggregations)."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.get("/{expense_id}")
async def get_expense(expense_id: int):
    """Get a single expense by ID."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.put("/{expense_id}")
async def update_expense(expense_id: int):
    """Update an expense entry."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}


@router.delete("/{expense_id}")
async def delete_expense(expense_id: int):
    """Soft-delete an expense entry."""
    # TODO: Phase 3 implementation
    return {"message": "Not yet implemented"}
