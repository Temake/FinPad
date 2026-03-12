from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer()

# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    """Extract and validate current user ID from JWT token."""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )
    return user_id


# Type alias for authenticated user dependency
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_user(
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from database."""
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# Type alias for full user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
