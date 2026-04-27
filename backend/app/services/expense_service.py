"""Expense service - CRUD operations for expenses."""

import uuid
from datetime import date, timedelta
from typing import Literal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import Expense, Category, ExpenseSource
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


DEFAULT_CATEGORY_SEED = [
    {"name": "Food & Groceries", "icon": "🍔", "color": "#FF6B6B"},
    {"name": "Transport", "icon": "🚗", "color": "#4ECDC4"},
    {"name": "Airtime & Data", "icon": "📱", "color": "#45B7D1"},
    {"name": "Bills & Utilities", "icon": "💡", "color": "#96CEB4"},
    {"name": "Shopping", "icon": "🛍️", "color": "#DDA0DD"},
    {"name": "Entertainment", "icon": "🎬", "color": "#FFD93D"},
    {"name": "Health", "icon": "💊", "color": "#6BCB77"},
    {"name": "Education", "icon": "📚", "color": "#4D96FF"},
    {"name": "Family & Gifts", "icon": "🎁", "color": "#FF8B94"},
    {"name": "Savings", "icon": "💰", "color": "#2ECC71"},
    {"name": "Other", "icon": "📦", "color": "#95A5A6"},
]


async def ensure_default_categories(db: AsyncSession) -> None:
    """Idempotently restore missing system categories."""
    result = await db.execute(
        select(Category.name).where(Category.user_id == None)
    )
    existing_names = {name for name in result.scalars().all()}

    missing_categories = [
        Category(name=item["name"], icon=item["icon"], color=item["color"], is_custom=False)
        for item in DEFAULT_CATEGORY_SEED
        if item["name"] not in existing_names
    ]

    if missing_categories:
        db.add_all(missing_categories)
        await db.flush()


async def create_expense(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ExpenseCreate,
    source: ExpenseSource = ExpenseSource.MANUAL,
) -> Expense:
    """Create a new expense."""
    expense = Expense(
        user_id=user_id,
        amount=data.amount,
        description=data.description,
        category_id=data.category_id,
        expense_date=data.expense_date,
        receipt_url=data.receipt_url,
        source=source,
    )
    db.add(expense)
    # Use flush() instead of commit() — the get_db() dependency auto-commits
    # when the request completes.  Committing here caused a double-commit that
    # corrupted the async session, producing the "session error" on expense
    # logging via WhatsApp.
    await db.flush()
    await db.refresh(expense)
    return expense


async def get_expense_by_id(
    db: AsyncSession, expense_id: int, user_id: uuid.UUID
) -> Expense | None:
    """Get expense by ID (only if owned by user)."""
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            Expense.id == expense_id,
            Expense.user_id == user_id,
            Expense.is_deleted == False,
        )
    )
    return result.scalar_one_or_none()


async def list_expenses(
    db: AsyncSession,
    user_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Expense]:
    """List expenses with optional filters."""
    query = (
        select(Expense)
        .options(selectinload(Expense.category))
        .where(Expense.user_id == user_id, Expense.is_deleted == False)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
    )

    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)
    if category_id:
        query = query.where(Expense.category_id == category_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_expense(
    db: AsyncSession, expense_id: int, user_id: uuid.UUID, data: ExpenseUpdate
) -> Expense | None:
    """Update an expense."""
    expense = await get_expense_by_id(db, expense_id, user_id)
    if not expense:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    await db.flush()
    await db.refresh(expense)
    return expense


async def delete_expense(
    db: AsyncSession, expense_id: int, user_id: uuid.UUID
) -> bool:
    """Soft delete an expense."""
    expense = await get_expense_by_id(db, expense_id, user_id)
    if not expense:
        return False

    expense.is_deleted = True
    await db.flush()
    return True


async def get_expense_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    period: Literal["daily", "weekly", "monthly"] = "monthly",
    target_date: date | None = None,
) -> dict:
    """Get expense summary for a period."""
    target = target_date or date.today()

    if period == "daily":
        start = target
        end = target
    elif period == "weekly":
        start = target - timedelta(days=target.weekday())  # Monday
        end = start + timedelta(days=6)  # Sunday
    else:  # monthly
        start = target.replace(day=1)
        # Last day of month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)

    # Total sum and count
    total_query = select(
        func.coalesce(func.sum(Expense.amount), 0).label("total"),
        func.count(Expense.id).label("count"),
    ).where(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= start,
        Expense.expense_date <= end,
    )
    total_result = await db.execute(total_query)
    row = total_result.one()
    total = float(row.total)
    count = row.count

    # By category
    category_query = (
        select(
            Category.name,
            func.coalesce(func.sum(Expense.amount), 0).label("amount"),
        )
        .join(Expense, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.expense_date >= start,
            Expense.expense_date <= end,
        )
        .group_by(Category.name)
    )
    category_result = await db.execute(category_query)
    by_category = {row.name: float(row.amount) for row in category_result.all()}

    return {
        "total": total,
        "count": count,
        "by_category": by_category,
        "period": period,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }


async def get_all_categories(db: AsyncSession, user_id: uuid.UUID | None = None) -> list[Category]:
    """Get all categories (system + user's custom)."""
    await ensure_default_categories(db)
    query = select(Category).where(
        (Category.user_id == None) | (Category.user_id == user_id)
    ).order_by(Category.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_custom_category(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    icon: str | None = None,
    color: str | None = None,
) -> Category:
    """Create a custom category for a user."""
    category = Category(
        name=name,
        icon=icon or "📦",
        color=color or "#95A5A6",
        is_custom=True,
        user_id=user_id,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category
