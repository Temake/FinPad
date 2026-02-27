"""SMS fallback service via Termii."""

import httpx
from app.core.config import get_settings

settings = get_settings()


class TermiiService:
    """Send SMS messages via Termii (paid fallback)."""

    BASE_URL = "https://api.ng.termii.com/api"

    def __init__(self):
        self.api_key = settings.TERMII_API_KEY
        self.sender_id = settings.TERMII_SENDER_ID

    async def send_otp(self, phone: str, otp: str) -> bool:
        """Send OTP via SMS through Termii (~₦4/message)."""
        if not self.api_key:
            return False

        formatted_phone = phone.replace("+", "").replace(" ", "").replace("-", "")

        payload = {
            "to": formatted_phone,
            "from": self.sender_id,
            "sms": f"Your FinPad verification code is: {otp}. Expires in {settings.OTP_EXPIRE_MINUTES} mins.",
            "type": "plain",
            "api_key": self.api_key,
            "channel": "generic",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.BASE_URL}/sms/send",
                    json=payload,
                )
                return response.status_code == 200
        except httpx.RequestError:
            return False
