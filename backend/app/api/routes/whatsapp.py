"""WhatsApp webhook routes - handles incoming messages from Evolution API."""

import logging
from datetime import date

from fastapi import APIRouter, Request

from app.api.deps import DbSession
from app.core.ai_service import parse_expense_text
from app.models.expense import ExpenseSource
from app.services.expense_service import (
    create_expense,
    get_expense_summary,
    get_all_categories,
)
from app.services.user_service import get_user_by_phone, get_or_create_user
from app.services.whatsapp_service import WhatsAppService
from app.schemas.expense import ExpenseCreate

logger = logging.getLogger(__name__)

router = APIRouter()

# Track users mid-registration (awaiting YES confirmation)
_pending_registrations: set[str] = set()


def _extract_phone_from_webhook(data: dict) -> str | None:
    """Extract the sender phone number from Evolution API webhook payload."""
    try:
        # Evolution API v2 payload structure
        if "data" in data:
            key = data["data"].get("key", {})
            remote_jid = key.get("remoteJid", "")
            # remoteJid is like "2348012345678@s.whatsapp.net"
            return remote_jid.split("@")[0] if "@" in remote_jid else None
        return None
    except (KeyError, AttributeError):
        return None


def _extract_message_text(data: dict) -> str | None:
    """Extract the message text from Evolution API webhook payload."""
    try:
        if "data" in data:
            message = data["data"].get("message", {})
            # Text messages
            if "conversation" in message:
                return message["conversation"]
            # Extended text
            if "extendedTextMessage" in message:
                return message["extendedTextMessage"].get("text")
        return None
    except (KeyError, AttributeError):
        return None


def _extract_whatsapp_id(data: dict) -> str | None:
    """Extract the WhatsApp JID as unique identifier."""
    try:
        if "data" in data:
            key = data["data"].get("key", {})
            return key.get("remoteJid")
        return None
    except (KeyError, AttributeError):
        return None


def _format_currency(amount: float) -> str:
    """Format amount as Nigerian Naira."""
    if amount >= 1000:
        return f"₦{amount:,.0f}"
    return f"₦{amount:.2f}"


def _format_summary(summary: dict, period_name: str) -> str:
    """Format expense summary as WhatsApp message."""
    total = summary["total"]
    count = summary["count"]
    by_category = summary["by_category"]

    if count == 0:
        return f"📊 *{period_name} Summary*\n\nNo expenses logged yet!"

    msg = f"📊 *{period_name} Summary*\n\n"
    msg += f"💰 Total: *{_format_currency(total)}*\n"
    msg += f"📝 {count} transaction{'s' if count != 1 else ''}\n\n"

    if by_category:
        msg += "*By Category:*\n"
        # Sort by amount descending
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
        for cat, amt in sorted_cats[:5]:  # Top 5
            pct = (amt / total * 100) if total > 0 else 0
            msg += f"• {cat}: {_format_currency(amt)} ({pct:.0f}%)\n"

    return msg


async def _handle_user_message(db, user, message_text: str, whatsapp: WhatsAppService) -> str | None:
    """Process a message from a registered user and return response."""
    text_lower = message_text.lower().strip()
    name = user.display_name or ""
    greeting = f" {name}" if name else ""

    # Greetings
    if text_lower in ("hi", "hello", "hey", "start", "yo"):
        return (
            f"👋 Hey{greeting}! Ready to track your spending?\n\n"
            f"• Send \"Spent 2000 on food\" to log\n"
            f"• Send \"Summary\" to see spending\n"
            f"• Send \"Help\" for all commands"
        )

    # Help
    if text_lower == "help":
        return (
            "📋 *FinPad Commands*\n\n"
            "*Log Expenses:*\n"
            "• \"Spent 2000 on transport\"\n"
            "• \"Bought suya 1.5k\"\n"
            "• \"Paid 5000 electricity bill\"\n\n"
            "*View Spending:*\n"
            "• \"Summary\" — Today's expenses\n"
            "• \"Week\" — This week's summary\n"
            "• \"Month\" — This month's summary\n\n"
            "💡 I use AI to auto-categorize your expenses!"
        )

    # Summary commands
    if text_lower in ("summary", "today"):
        summary = await get_expense_summary(db, user.id, "daily")
        return _format_summary(summary, "Today's")

    if text_lower == "week":
        summary = await get_expense_summary(db, user.id, "weekly")
        return _format_summary(summary, "This Week's")

    if text_lower == "month":
        summary = await get_expense_summary(db, user.id, "monthly")
        return _format_summary(summary, "This Month's")

    # Try to parse as expense
    try:
        parsed = await parse_expense_text(message_text)

        if parsed.get("amount"):
            # Find category ID
            categories = await get_all_categories(db, user.id)
            category_map = {c.name.lower(): c.id for c in categories}
            category_name = parsed.get("category", "Other")
            category_id = category_map.get(category_name.lower(), category_map.get("other", 1))

            # Create expense
            expense_data = ExpenseCreate(
                amount=parsed["amount"],
                description=parsed.get("description") or message_text[:100],
                category_id=category_id,
                expense_date=date.today(),
            )
            expense = await create_expense(db, user.id, expense_data, source=ExpenseSource.WHATSAPP)

            confidence = parsed.get("confidence", 0.5)
            confidence_emoji = "✅" if confidence > 0.8 else "🤔"

            return (
                f"{confidence_emoji} *Expense Logged!*\n\n"
                f"💵 Amount: *{_format_currency(parsed['amount'])}*\n"
                f"📝 {parsed.get('description', message_text[:50])}\n"
                f"🏷️ Category: {category_name}\n\n"
                f"_Logged via WhatsApp_"
            )
        else:
            # Couldn't extract amount
            return (
                "🤔 I couldn't find an amount in your message.\n\n"
                "Try formats like:\n"
                "• \"Spent 2000 on transport\"\n"
                "• \"Bought rice 5k\"\n"
                "• \"Paid 1500 for data\""
            )

    except Exception as e:
        logger.error(f"Error processing expense message: {e}")
        return (
            "😅 Oops! Something went wrong.\n\n"
            "Try sending your expense again, like:\n"
            "\"Spent 2000 on transport\""
        )


@router.post("/webhook")
async def whatsapp_webhook(request: Request, db: DbSession):
    """
    Receive incoming WhatsApp messages from Evolution API.

    Handles:
    - New user registration (no OTP - just YES confirmation)
    - Message routing for registered users (Phase 5 will expand this)
    """
    data = await request.json()
    logger.debug(f"WhatsApp webhook received: {data}")

    # Only process message events
    event = data.get("event")
    if event != "messages.upsert":
        return {"status": "ignored", "event": event}

    # Ignore messages sent by us (prevent self-reply loops)
    try:
        from_me = data.get("data", {}).get("key", {}).get("fromMe", False)
        if from_me:
            return {"status": "ignored", "reason": "fromMe"}
    except (KeyError, AttributeError):
        pass

    phone = _extract_phone_from_webhook(data)
    message_text = _extract_message_text(data)
    whatsapp_id = _extract_whatsapp_id(data)

    if not phone or not message_text:
        return {"status": "ignored", "reason": "no phone or message"}

    message_text = message_text.strip()
    whatsapp = WhatsAppService()

    # Check if user exists
    existing_user = await get_user_by_phone(db, phone)

    if existing_user:
        # User is registered — handle commands
        response = await _handle_user_message(db, existing_user, message_text, whatsapp)
        if response:
            await whatsapp.send_text(phone, response)
        return {"status": "processed", "user": "existing"}

    # New user — registration flow
    if phone in _pending_registrations:
        # They were asked to confirm — check for YES
        if message_text.upper() in ("YES", "Y", "YEAH", "YEP", "OK", "OKAY"):
            _pending_registrations.discard(phone)

            # Create account — no OTP needed (WhatsApp already verified)
            user, _ = await get_or_create_user(db, phone, whatsapp_id=whatsapp_id)

            await whatsapp.send_welcome(phone)
            logger.info(f"New user registered via WhatsApp: {phone}")

            return {"status": "registered", "phone": phone}
        else:
            _pending_registrations.discard(phone)
            await whatsapp.send_text(
                phone,
                "No worries! Send *Hi* anytime if you change your mind. 👋",
            )
            return {"status": "registration_declined"}

    # First contact — ask to confirm registration
    _pending_registrations.add(phone)
    await whatsapp.send_text(
        phone,
        f"👋 Welcome to *FinPad*!\n\n"
        f"I help you track expenses and build smart money habits.\n\n"
        f"To get started, I'll register you with this WhatsApp number:\n"
        f"*+{phone}*\n\n"
        f"Reply *YES* to confirm.",
    )

    return {"status": "pending_confirmation", "phone": phone}


@router.get("/webhook")
async def whatsapp_webhook_verify():
    """Webhook verification / health check for Evolution API."""
    return {"status": "ok", "service": "finpad-whatsapp"}


# --- Notification Trigger Endpoints (for scheduled tasks / cron) ---

@router.post("/notifications/daily-reminders")
async def trigger_daily_reminders(db: DbSession):
    """
    Trigger daily reminder notifications.
    
    This should be called by a cron job every hour.
    Users receive reminders at their preferred time (daily_reminder_time).
    """
    from app.services.notification_service import send_daily_reminders
    
    result = await send_daily_reminders(db)
    return {
        "status": "completed",
        "sent": result["sent"],
        "total_users": result["total_users"],
        "errors": result["errors"][:5] if result["errors"] else [],  # Limit errors in response
    }


@router.post("/notifications/weekly-summaries")
async def trigger_weekly_summaries(db: DbSession):
    """
    Trigger weekly summary notifications.
    
    This should be called by a cron job once per week (e.g., Sunday 6pm).
    """
    from app.services.notification_service import send_weekly_summaries
    
    result = await send_weekly_summaries(db)
    return {
        "status": "completed",
        "sent": result["sent"],
        "total_users": result["total_users"],
        "errors": result["errors"][:5] if result["errors"] else [],
    }

