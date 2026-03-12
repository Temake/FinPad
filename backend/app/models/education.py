"""SQLAlchemy model for financial education tips."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FinancialTip(Base):
    """Financial micro-tips for user education."""
    
    __tablename__ = "financial_tips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # Categories: savings, budgeting, investing, debt_management, general
    
    icon: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Emoji
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<FinancialTip {self.id}: {self.title[:30]}>"
