"""Expense routes - CRUD and summary endpoints."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserId, DbSession
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseSummary,
    CategoryResponse,
)
from app.services import expense_service

router = APIRouter()


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Create a new expense entry."""
    expense = await expense_service.create_expense(db, user_id, data)
    return _expense_to_response(expense)


@router.get("/", response_model=list[ExpenseResponse])
async def list_expenses(
    db: DbSession,
    user_id: CurrentUserId,
    start_date: date | None = Query(None, description="Filter from date"),
    end_date: date | None = Query(None, description="Filter to date"),
    category_id: int | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List expenses with filters (date range, category, etc.)."""
    expenses = await expense_service.list_expenses(
        db, user_id, start_date, end_date, category_id, limit, offset
    )
    return [_expense_to_response(e) for e in expenses]


@router.get("/summary", response_model=ExpenseSummary)
async def expense_summary(
    db: DbSession,
    user_id: CurrentUserId,
    period: Literal["daily", "weekly", "monthly"] = Query("monthly"),
    target_date: date | None = Query(None, description="Date within target period"),
):
    """Get expense summary (daily/weekly/monthly aggregations)."""
    summary = await expense_service.get_expense_summary(db, user_id, period, target_date)
    return summary


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: DbSession,
    user_id: CurrentUserId,
):
    """Get all available categories (system + user custom)."""
    categories = await expense_service.get_all_categories(db, user_id)
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            icon=c.icon,
            color=c.color,
            is_custom=c.is_custom,
        )
        for c in categories
    ]


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Get a single expense by ID."""
    expense = await expense_service.get_expense_by_id(db, expense_id, user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _expense_to_response(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Update an expense entry."""
    expense = await expense_service.update_expense(db, expense_id, user_id, data)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _expense_to_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Soft-delete an expense entry."""
    deleted = await expense_service.delete_expense(db, expense_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return None


def _expense_to_response(expense) -> ExpenseResponse:
    """Convert Expense model to response schema."""
    return ExpenseResponse(
        id=expense.id,
        amount=float(expense.amount),
        currency=expense.currency,
        description=expense.description,
        expense_date=expense.expense_date,
        category_id=expense.category_id,
        category_name=expense.category.name if expense.category else None,
        category_icon=expense.category.icon if expense.category else None,
        source=expense.source.value,
        created_at=expense.created_at.isoformat(),
    )
