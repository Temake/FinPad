"""Pydantic schemas for AI-powered features."""

from pydantic import BaseModel, Field


class ParseExpenseRequest(BaseModel):
    """Request to parse natural language expense."""
    text: str = Field(..., min_length=1, max_length=500, description="Expense description to parse")


class ParsedExpenseResponse(BaseModel):
    """AI-parsed expense data."""
    amount: float | None = Field(None, description="Extracted amount in Naira")
    description: str | None = Field(None, description="Cleaned description")
    category: str = Field(..., description="Suggested category name")
    category_id: int | None = Field(None, description="Matching category ID if found")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")


class ReceiptUploadResponse(BaseModel):
    """Extracted data from receipt image."""
    merchant: str | None = Field(None, description="Store/merchant name")
    amount: float | None = Field(None, description="Total amount in Naira")
    items: list[str] = Field(default_factory=list, description="List of items")
    date: str | None = Field(None, description="Receipt date (YYYY-MM-DD)")
    category: str = Field(..., description="Suggested category")
    category_id: int | None = Field(None, description="Matching category ID")
    confidence: float = Field(..., ge=0, le=1, description="OCR confidence score")


class SmartExpenseCreate(BaseModel):
    """Create expense with AI assistance."""
    text: str | None = Field(None, description="Natural language description (AI will parse)")
    amount: float | None = Field(None, gt=0, description="Manual amount override")
    description: str | None = Field(None, description="Manual description override")
    category_id: int | None = Field(None, description="Manual category override")
    expense_date: str | None = Field(None, description="Date override (YYYY-MM-DD)")
    use_ai: bool = Field(True, description="Whether to use AI for parsing")


class AIStatusResponse(BaseModel):
    """AI service status."""
    configured: bool
    model: str
    features: list[str]
