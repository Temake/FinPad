"""Pydantic schemas for financial education."""

from datetime import datetime
from pydantic import BaseModel


class FinancialTipBase(BaseModel):
    """Base financial tip schema."""
    title: str
    content: str
    category: str
    icon: str | None = None


class FinancialTipResponse(FinancialTipBase):
    """Financial tip response schema."""
    id: int

    model_config = {"from_attributes": True}


class DailyTipResponse(BaseModel):
    """Daily tip with context."""
    tip: FinancialTipResponse
    tip_number: int  # e.g., "Tip #42"
    category_emoji: str  # Category-specific emoji


class TipHistoryResponse(BaseModel):
    """History of tips sent to user."""
    tips: list[FinancialTipResponse]
    total_tips_received: int
