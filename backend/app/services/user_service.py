"""User service - database operations for user management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.gamification import UserStats


async def get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    """Find a user by phone number."""
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Find a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_whatsapp_id(db: AsyncSession, whatsapp_id: str) -> User | None:
    """Find a user by WhatsApp ID."""
    result = await db.execute(select(User).where(User.whatsapp_id == whatsapp_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    phone: str,
    whatsapp_id: str | None = None,
    display_name: str | None = None,
) -> User:
    """Create a new user and initialize their stats."""
    user = User(
        phone=phone,
        whatsapp_id=whatsapp_id,
        whatsapp_linked=whatsapp_id is not None,
        display_name=display_name,
    )
    db.add(user)
    await db.flush()  # Get the user ID before creating stats

    # Initialize user stats
    stats = UserStats(user_id=user.id)
    db.add(stats)

    return user


async def get_or_create_user(
    db: AsyncSession,
    phone: str,
    whatsapp_id: str | None = None,
) -> tuple[User, bool]:
    """Get existing user or create a new one. Returns (user, is_new)."""
    user = await get_user_by_phone(db, phone)
    if user:
        # Update WhatsApp link if provided and not yet linked
        if whatsapp_id and not user.whatsapp_linked:
            user.whatsapp_id = whatsapp_id
            user.whatsapp_linked = True
        return user, False

    user = await create_user(db, phone, whatsapp_id)
    return user, True


async def update_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    **fields,
) -> User | None:
    """Update user profile fields."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    for key, value in fields.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)

    return user


async def link_whatsapp(
    db: AsyncSession,
    user_id: uuid.UUID,
    whatsapp_id: str,
) -> User | None:
    """Link a WhatsApp ID to an existing user."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.whatsapp_id = whatsapp_id
    user.whatsapp_linked = True
    return user
