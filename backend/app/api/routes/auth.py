"""Authentication routes - OTP-based phone auth with JWT tokens."""

import uuid
import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserId, DbSession
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.redis import get_redis
from app.schemas.auth import PhoneRequest, OTPVerifyRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserProfile
from app.services.otp_service import OTPService
from app.services.otp_delivery import deliver_otp
from app.services.user_service import get_or_create_user, get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalize_phone(phone: str) -> str:
    """Normalize phone: strip spaces/dashes, ensure starts with 234."""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    # If starts with 0, replace with 234 (Nigerian local format)
    if phone.startswith("0"):
        phone = "234" + phone[1:]
    return phone


@router.post("/request-otp")
async def request_otp(request: PhoneRequest):
    """
    Request an OTP for web app login.
    Sends OTP via WhatsApp (free) first, falls back to SMS.
    """
    phone = _normalize_phone(request.phone)

    otp_service = OTPService(redis_client=get_redis())

    # Rate limit: don't send if there's already an active OTP
    if await otp_service.has_active_otp(phone):
        return {
            "message": "OTP already sent. Please wait for it to expire before requesting a new one.",
            "phone": phone,
        }

    # Generate OTP
    otp = await otp_service.create_otp(phone)

    # Deliver via WhatsApp → SMS fallback
    delivery_result = await deliver_otp(phone, otp)

    if not delivery_result["success"]:
        # In development, log the OTP so testing is possible
        logger.warning(f"OTP delivery failed for {phone}. OTP for testing: {otp}")
        return {
            "message": "OTP generated but delivery services unavailable. Check server logs for testing.",
            "phone": phone,
        }

    return {
        "message": f"OTP sent via {delivery_result['method']}",
        "phone": phone,
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerifyRequest, db: DbSession):
    """
    Verify OTP and issue JWT access + refresh tokens.
    Creates a new user account if the phone doesn't exist yet.
    """
    phone = _normalize_phone(request.phone)

    otp_service = OTPService(redis_client=get_redis())

    # Verify OTP
    is_valid = await otp_service.verify_otp(phone, request.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # Get or create user
    user, is_new = await get_or_create_user(db, phone)

    if is_new:
        logger.info(f"New user registered: {phone}")

    # Issue tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """Issue a new access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is not a refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    token_data = {"sub": user_id}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user(user_id: CurrentUserId, db: DbSession):
    """Get the authenticated user's profile."""
    user = await get_user_by_id(db, uuid.UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get stats
    streak = 0
    level = "Beginner Saver"
    if user.user_stats:
        streak = user.user_stats.current_streak
        level = user.user_stats.level

    return UserProfile(
        id=user.id,
        phone=user.phone,
        display_name=user.display_name,
        currency=user.currency,
        notification_enabled=user.notification_enabled,
        daily_reminder_time=user.daily_reminder_time,
        whatsapp_linked=user.whatsapp_linked,
        current_streak=streak,
        level=level,
    )
