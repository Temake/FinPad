"""OTP generation and verification service using Redis."""

import random
import string
from app.core.config import get_settings

settings = get_settings()


class OTPService:
    """Generate and verify OTPs stored in Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.expire_seconds = settings.OTP_EXPIRE_MINUTES * 60
        self.otp_length = settings.OTP_LENGTH

    def _generate_otp(self) -> str:
        """Generate a random numeric OTP."""
        return "".join(random.choices(string.digits, k=self.otp_length))

    async def create_otp(self, phone: str) -> str:
        """Generate and store an OTP for a phone number."""
        otp = self._generate_otp()
        key = f"otp:{phone}"

        if self.redis:
            await self.redis.setex(key, self.expire_seconds, otp)
        else:
            # Fallback: in-memory store (dev only)
            if not hasattr(self, "_store"):
                self._store = {}
            self._store[key] = otp

        return otp

    async def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify an OTP for a phone number."""
        key = f"otp:{phone}"

        if self.redis:
            stored_otp = await self.redis.get(key)
            if stored_otp and stored_otp.decode() == otp:
                await self.redis.delete(key)  # One-time use
                return True
        else:
            # Fallback: in-memory store (dev only)
            stored_otp = getattr(self, "_store", {}).get(key)
            if stored_otp == otp:
                del self._store[key]
                return True

        return False
