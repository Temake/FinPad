"""SQLAlchemy models for expenses and categories."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

import enum


class ExpenseSource(str, enum.Enum):
    MANUAL = "manual"
    WHATSAPP = "whatsapp"
    BANK_SYNC = "bank_sync"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=True)  # emoji or icon name
    color: Mapped[str] = mapped_column(String(7), nullable=True)  # hex color
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)

    # null user_id = default system category; set user_id = custom user category
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    expenses = relationship("Expense", back_populates="category", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    source: Mapped[ExpenseSource] = mapped_column(
        Enum(
            ExpenseSource,
            name="expense_source",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=ExpenseSource.MANUAL,
    )
    receipt_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense {self.amount} {self.currency}>"
