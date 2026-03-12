"""Import all models so Alembic can discover them."""

from app.models.user import User  
from app.models.expense import Category, Expense, ExpenseSource  
from app.models.gamification import Badge, UserBadge, UserStats
from app.models.education import FinancialTip

__all__ = [
    "User",
    "Category",
    "Expense",
    "ExpenseSource",
    "Badge",
    "UserBadge",
    "UserStats",
    "FinancialTip",
]
