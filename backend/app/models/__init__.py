"""Import all models so Alembic can discover them."""

from app.models.user import User  # noqa: F401
from app.models.expense import Category, Expense, ExpenseSource  # noqa: F401
from app.models.gamification import Badge, UserBadge, UserStats  # noqa: F401

__all__ = [
    "User",
    "Category",
    "Expense",
    "ExpenseSource",
    "Badge",
    "UserBadge",
    "UserStats",
]
