"""Pydantic schemas for user profiles."""

import uuid
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile response."""
    id: uuid.UUID
    phone: str
    display_name: str | None
    currency: str
    notification_enabled: bool
    daily_reminder_time: str | None
    whatsapp_linked: bool
    current_streak: int = 0
    level: str = "Beginner Saver"

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Update user profile."""
    display_name: str | None = Field(None, max_length=100)
    currency: str | None = Field(None, max_length=3)
    notification_enabled: bool | None = None
    daily_reminder_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
