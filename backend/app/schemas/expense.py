"""Pydantic schemas for expenses."""

from datetime import date
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    """Create a new expense."""
    amount: float = Field(..., gt=0, description="Expense amount")
    description: str | None = Field(None, max_length=500)
    category_id: int | None = None
    expense_date: date = Field(default_factory=date.today)
    receipt_url: str | None = None


class ExpenseUpdate(BaseModel):
    """Update an existing expense."""
    amount: float | None = Field(None, gt=0)
    description: str | None = None
    category_id: int | None = None
    expense_date: date | None = None


class ExpenseResponse(BaseModel):
    """Expense response with category info."""
    id: int
    amount: float
    currency: str
    description: str | None
    expense_date: date
    category_id: int | None = None
    category_name: str | None = None
    category_icon: str | None = None
    source: str
    created_at: str

    model_config = {"from_attributes": True}


class ExpenseSummary(BaseModel):
    """Aggregated expense summary."""
    total: float
    count: int
    by_category: dict[str, float] = {}
    period: str  # "daily", "weekly", "monthly"
    start_date: str
    end_date: str


class CategoryResponse(BaseModel):
    """Category response."""
    id: int
    name: str
    icon: str | None
    color: str | None
    is_custom: bool
