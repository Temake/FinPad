"""Authentication routes - Phase 2 implementation."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/request-otp")
async def request_otp():
    """Request OTP for web app login. Sends via WhatsApp (free) or SMS (fallback)."""
    # TODO: Phase 2 implementation
    return {"message": "Not yet implemented"}


@router.post("/verify-otp")
async def verify_otp():
    """Verify OTP and issue JWT tokens."""
    # TODO: Phase 2 implementation
    return {"message": "Not yet implemented"}


@router.post("/refresh")
async def refresh_token():
    """Refresh an expired access token."""
    # TODO: Phase 2 implementation
    return {"message": "Not yet implemented"}


@router.get("/me")
async def get_current_user():
    """Get current authenticated user profile."""
    # TODO: Phase 2 implementation
    return {"message": "Not yet implemented"}
