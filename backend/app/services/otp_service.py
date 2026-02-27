"""OTP generation and verification service using Redis."""

import random
import string
from app.core.config import get_settings

settings = get_settings()

# In-memory fallback store for development without Redis
_memory_store: dict[str, str] = {}


class OTPService:
    """Generate and verify OTPs stored in Redis (or in-memory fallback)."""

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
            _memory_store[key] = otp

        return otp

    async def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify an OTP for a phone number. One-time use."""
        key = f"otp:{phone}"

        if self.redis:
            stored_otp = await self.redis.get(key)
            if stored_otp and stored_otp == otp:
                await self.redis.delete(key)
                return True
        else:
            stored_otp = _memory_store.get(key)
            if stored_otp and stored_otp == otp:
                del _memory_store[key]
                return True

        return False

    async def has_active_otp(self, phone: str) -> bool:
        """Check if there's already an active OTP (rate limiting)."""
        key = f"otp:{phone}"
        if self.redis:
            return await self.redis.exists(key) > 0
        return key in _memory_store
