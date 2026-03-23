"""WhatsApp messaging service via Evolution API."""

import httpx
from app.core.config import get_settings

settings = get_settings()


def _format_currency(amount: float) -> str:
    """Format amount as Nigerian Naira."""
    if amount >= 1000:
        return f"₦{amount:,.0f}"
    return f"₦{amount:.2f}"


class WhatsAppService:
    """Send messages via Evolution API (self-hosted WhatsApp gateway)."""

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.instance = settings.EVOLUTION_INSTANCE
        api_key = settings.EVOLUTION_API_GLOBAL_KEY or settings.EVOLUTION_API_KEY
        if not api_key:
            raise ValueError("Evolution API key is not configured")
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
        }

    async def send_text(self, phone: str, message: str) -> bool:
        """Send a text message to a WhatsApp number."""
        formatted_phone = phone.replace("+", "").replace(" ", "").replace("-", "")

        payload = {
            "number": formatted_phone,
            "text": message,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/message/sendText/{self.instance}",
                    json=payload,
                    headers=self.headers,
                )
                return response.status_code == 200
        except httpx.RequestError:
            return False

    async def send_otp(self, phone: str, otp: str) -> bool:
        """Send an OTP verification message."""
        message = (
            f"🔐 *FinPad Verification*\n\n"
            f"Your OTP is: *{otp}*\n\n"
            f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            f"Don't share this code with anyone."
        )
        return await self.send_text(phone, message)

    async def send_welcome(self, phone: str) -> bool:
        """Send welcome message to a new WhatsApp user."""
        message = (
            "👋 *Welcome to FinPad!*\n\n"
            "I help you track expenses and build smart money habits.\n\n"
            "Here's what you can do:\n"
            "• Send *\"Spent 2000 on food\"* to log an expense\n"
            "• Send *\"Summary\"* to see your spending\n"
            "• Send *\"Help\"* for all commands\n\n"
            "💡 I'll remind you daily to log your expenses!"
        )
        return await self.send_text(phone, message)

    async def send_daily_reminder(self, phone: str) -> bool:
        """Send daily expense logging reminder."""
        message = (
            "📝 *Daily Reminder*\n\n"
            "Don't forget to log today's expenses!\n\n"
            "Just tell me what you spent, e.g.:\n"
            "\"Spent 1500 on transport\""
        )
        return await self.send_text(phone, message)

    async def send_weekly_summary(
        self, phone: str, total: float, count: int, top_category: str | None = None
    ) -> bool:
        """Send weekly spending summary."""
        top_part = f"\n🏷️ Top category: {top_category}" if top_category else ""
        message = (
            f"📊 *Weekly Summary*\n\n"
            f"You spent *{_format_currency(total)}* this week\n"
            f"📝 {count} transaction{'s' if count != 1 else ''}{top_part}\n\n"
            f"Keep tracking to stay on top of your finances! 💪"
        )
        return await self.send_text(phone, message)

    async def send_streak_achievement(self, phone: str, days: int) -> bool:
        """Send streak achievement notification."""
        emoji = "🔥" if days >= 7 else "⭐"
        if days == 7:
            msg = f"{emoji} *7-Day Streak!*\n\nYou've logged expenses for a whole week! Keep it up!"
        elif days == 30:
            msg = f"🏆 *30-Day Streak!*\n\nIncredible! A full month of tracking. You're a finance pro!"
        else:
            msg = f"{emoji} *{days}-Day Streak!*\n\nYou've logged expenses {days} days in a row!"
        return await self.send_text(phone, msg)

    async def send_expense_confirmation(
        self, phone: str, amount: float, description: str, category: str
    ) -> bool:
        """Send expense logged confirmation."""
        message = (
            f"✅ *Expense Logged!*\n\n"
            f"💵 Amount: *{_format_currency(amount)}*\n"
            f"📝 {description}\n"
            f"🏷️ Category: {category}"
        )
        return await self.send_text(phone, message)
