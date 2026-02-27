"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field


class PhoneRequest(BaseModel):
    """Request OTP for a phone number."""
    phone: str = Field(..., description="Phone number with country code, e.g. 2348012345678")


class OTPVerifyRequest(BaseModel):
    """Verify OTP for login."""
    phone: str = Field(..., description="Phone number used in OTP request")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request a new access token using refresh token."""
    refresh_token: str
