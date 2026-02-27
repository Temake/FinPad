"""SQLAlchemy model for users."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # WhatsApp integration
    whatsapp_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    whatsapp_linked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Preferences
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_reminder_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True, default="20:00"
    )  # HH:MM format

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    expenses = relationship("Expense", back_populates="user", lazy="selectin")
    user_badges = relationship("UserBadge", back_populates="user", lazy="selectin")
    user_stats = relationship("UserStats", back_populates="user", uselist=False, lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.phone}>"
