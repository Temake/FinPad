"""WhatsApp webhook routes - handles incoming messages from Evolution API."""

import json
import logging
import re
import time
from datetime import date

from fastapi import APIRouter, Request

from app.api.deps import DbSession
from app.core.ai_service import parse_expense_text
from app.core.redis import get_redis
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
_processed_message_ids: set[str] = set()

PENDING_REGISTRATION_TTL_SECONDS = 15 * 60
PROCESSED_MESSAGE_TTL_SECONDS = 24 * 60 * 60
CONFIRMATION_WORDS = {"YES", "Y", "YEAH", "YEP", "OK", "OKAY"}
MAX_WEBHOOK_PAYLOAD_BYTES = 64 * 1024
MAX_MESSAGE_TEXT_CHARS = 1000
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_MESSAGES = 30

_rate_limit_tracker: dict[str, dict[str, float]] = {}


def _pending_key(phone: str) -> str:
    return f"whatsapp:pending_registration:{phone}"


def _processed_message_key(message_id: str) -> str:
    return f"whatsapp:processed_message:{message_id}"


def _canonicalize_text(value: str) -> str:
    """Normalize text for safe intent matching across punctuation and emoji."""
    upper = value.upper().strip()
    upper = re.sub(r"[^A-Z0-9\s]", " ", upper)
    return " ".join(upper.split())


def _is_confirmation_yes(message_text: str) -> bool:
    """Check if a confirmation reply means YES after canonicalization."""
    normalized = _canonicalize_text(message_text)
    if not normalized:
        return False
    tokens = normalized.split()
    if not tokens:
        return False
    return normalized in CONFIRMATION_WORDS or tokens[0] in CONFIRMATION_WORDS


async def _set_pending_registration(phone: str) -> None:
    """Persist pending registration state with TTL, fallback to in-memory set."""
    redis = get_redis()
    if redis:
        await redis.set(_pending_key(phone), "1", ex=PENDING_REGISTRATION_TTL_SECONDS)
    else:
        _pending_registrations.add(phone)


async def _has_pending_registration(phone: str) -> bool:
    """Check if registration confirmation is pending for a phone number."""
    redis = get_redis()
    if redis:
        return await redis.exists(_pending_key(phone)) > 0
    return phone in _pending_registrations


async def _clear_pending_registration(phone: str) -> None:
    """Clear pending registration state in both Redis and fallback memory."""
    redis = get_redis()
    if redis:
        await redis.delete(_pending_key(phone))
    _pending_registrations.discard(phone)


def _extract_message_id(data: dict) -> str | None:
    """Extract unique message ID for idempotency checks."""
    try:
        if "data" in data:
            key = data["data"].get("key", {})
            msg_id = key.get("id")
            if msg_id and isinstance(msg_id, str):
                return msg_id
        return None
    except (KeyError, AttributeError):
        return None


async def _is_processed_message(message_id: str) -> bool:
    """Check if message has already been handled."""
    redis = get_redis()
    if redis:
        return await redis.exists(_processed_message_key(message_id)) > 0
    return message_id in _processed_message_ids


async def _mark_processed_message(message_id: str) -> None:
    """Mark a message as processed with expiry to prevent replay effects."""
    redis = get_redis()
    if redis:
        await redis.set(_processed_message_key(message_id), "1", ex=PROCESSED_MESSAGE_TTL_SECONDS)
    else:
        _processed_message_ids.add(message_id)


def _is_valid_message_event_shape(data: dict) -> bool:
    """Validate minimum required payload structure before deeper processing."""
    if not isinstance(data, dict):
        return False
    if data.get("event") != "messages.upsert":
        return True

    payload = data.get("data")
    if not isinstance(payload, dict):
        return False

    key = payload.get("key")
    message = payload.get("message")

    if key is not None and not isinstance(key, dict):
        return False
    if message is not None and not isinstance(message, dict):
        return False
    return True


def _rate_limit_key(source: str) -> str:
    return f"whatsapp:ingress_rate:{source}"


async def _is_rate_limited(source: str) -> bool:
    """Basic per-source sliding-window limit with Redis and in-memory fallback."""
    redis = get_redis()
    if redis:
        key = _rate_limit_key(source)
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, RATE_LIMIT_WINDOW_SECONDS)
        return count > RATE_LIMIT_MAX_MESSAGES

    now = time.time()
    state = _rate_limit_tracker.get(source)
    if not state or (now - state["window_start"]) >= RATE_LIMIT_WINDOW_SECONDS:
        _rate_limit_tracker[source] = {"window_start": now, "count": 1}
        return False

    state["count"] += 1
    return state["count"] > RATE_LIMIT_MAX_MESSAGES


def _extract_phone_from_webhook(data: dict) -> str | None:
    """Extract the sender phone number from Evolution API webhook payload."""
    try:
        # Evolution API v2 payload structure
        if "data" in data:
            key = data["data"].get("key", {})
            sender_pn = key.get("senderPn", "")
            if isinstance(sender_pn, str) and "@" in sender_pn:
                candidate = sender_pn.split("@")[0]
                if candidate.isdigit():
                    return candidate

            participant = key.get("participant", "")
            if isinstance(participant, str) and participant.endswith("@s.whatsapp.net"):
                candidate = participant.split("@")[0]
                if candidate.isdigit():
                    return candidate

            remote_jid = key.get("remoteJid", "")
            if isinstance(remote_jid, str) and remote_jid.endswith("@s.whatsapp.net"):
                candidate = remote_jid.split("@")[0]
                if candidate.isdigit():
                    return candidate
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


# Canonicalized intent tokens for command matching.
# Using _canonicalize_text strips invisible Unicode characters WhatsApp may
# inject (zero-width spaces, RTL marks, soft hyphens, etc.) that break simple
# .lower().strip() comparisons.
_GREETING_WORDS = {"HI", "HELLO", "HEY", "START", "YO"}
_HELP_WORDS = {"HELP", "COMMANDS", "MENU"}
_SUMMARY_TODAY_WORDS = {"SUMMARY", "TODAY"}
_WEEK_WORDS = {"WEEK", "WEEKLY"}
_MONTH_WORDS = {"MONTH", "MONTHLY"}


async def _handle_user_message(db, user, message_text: str, whatsapp: WhatsAppService) -> str | None:
    """Process a message from a registered user and return response."""
    canon = _canonicalize_text(message_text)
    name = user.display_name or ""
    greeting = f" {name}" if name else ""

    # Greetings
    if canon in _GREETING_WORDS:
        return (
            f"👋 Hey{greeting}! Ready to track your spending?\n\n"
            f"• Send \"Spent 2000 on food\" to log\n"
            f"• Send \"Summary\" to see spending\n"
            f"• Send \"Help\" for all commands"
        )

    # Help
    if canon in _HELP_WORDS:
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
    if canon in _SUMMARY_TODAY_WORDS:
        summary = await get_expense_summary(db, user.id, "daily")
        return _format_summary(summary, "Today's")

    if canon in _WEEK_WORDS:
        summary = await get_expense_summary(db, user.id, "weekly")
        return _format_summary(summary, "This Week's")

    if canon in _MONTH_WORDS:
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
        await db.rollback()
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
    try:
        raw_body = await request.body()
        if len(raw_body) > MAX_WEBHOOK_PAYLOAD_BYTES:
            return {"status": "ignored", "reason": "payload_too_large"}

        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("WhatsApp webhook received invalid JSON payload")
        return {"status": "ignored", "reason": "invalid_json"}
    except Exception:
        logger.warning("WhatsApp webhook body could not be read")
        return {"status": "ignored", "reason": "invalid_payload"}

    logger.debug(f"WhatsApp webhook received: {data}")

    try:
        # Only process message events
        event = data.get("event")
        if event != "messages.upsert":
            return {"status": "ignored", "event": event}

        if not _is_valid_message_event_shape(data):
            return {"status": "ignored", "reason": "malformed_event_payload"}

        # Ignore messages sent by us (prevent self-reply loops)
        from_me = data.get("data", {}).get("key", {}).get("fromMe", False)
        if from_me:
            return {"status": "ignored", "reason": "fromMe"}

        message_id = _extract_message_id(data)
        if message_id and await _is_processed_message(message_id):
            return {"status": "ignored", "reason": "duplicate_event"}

        phone = _extract_phone_from_webhook(data)
        source = phone or (request.client.host if request.client else "unknown")
        if await _is_rate_limited(source):
            return {"status": "ignored", "reason": "rate_limited"}

        message_text = _extract_message_text(data)
        whatsapp_id = _extract_whatsapp_id(data)

        if not phone or not message_text:
            if message_id:
                await _mark_processed_message(message_id)
            return {"status": "ignored", "reason": "no phone or message"}

        message_text = message_text.strip()
        if not message_text:
            if message_id:
                await _mark_processed_message(message_id)
            return {"status": "ignored", "reason": "empty_message"}

        if len(message_text) > MAX_MESSAGE_TEXT_CHARS:
            if message_id:
                await _mark_processed_message(message_id)
            return {"status": "ignored", "reason": "message_too_large"}

        whatsapp = WhatsAppService()

        # Check if user exists
        existing_user = await get_user_by_phone(db, phone)

        if existing_user:
            # User is registered — handle commands
            response = await _handle_user_message(db, existing_user, message_text, whatsapp)
            if response:
                await whatsapp.send_text(phone, response)
            if message_id:
                await _mark_processed_message(message_id)
            return {"status": "processed", "user": "existing"}

        # New user — registration flow
        if await _has_pending_registration(phone):
            # They were asked to confirm — check for YES
            if _is_confirmation_yes(message_text):
                await _clear_pending_registration(phone)

                # Persist registration before sending outbound messages.
                # NOTE: Do NOT call db.commit() here — the get_db() dependency
                # auto-commits when the request finishes successfully.  Calling
                # commit() manually causes a double-commit that corrupts the
                # session state and breaks subsequent queries in the same request.
                _, _ = await get_or_create_user(db, phone, whatsapp_id=whatsapp_id)
                await db.flush()

                welcome_sent = await whatsapp.send_welcome(phone)
                if not welcome_sent:
                    logger.warning("User registered but welcome message failed for %s", phone)

                if message_id:
                    await _mark_processed_message(message_id)
                logger.info(f"New user registered via WhatsApp: {phone}")
                return {"status": "registered", "phone": phone, "welcome_sent": welcome_sent}

            await _clear_pending_registration(phone)
            await whatsapp.send_text(
                phone,
                "No worries! Send *Hi* anytime if you change your mind. 👋",
            )
            if message_id:
                await _mark_processed_message(message_id)
            return {"status": "registration_declined"}

        # First contact — ask to confirm registration
        await _set_pending_registration(phone)
        await whatsapp.send_text(
            phone,
            f"👋 Welcome to *FinPad*!\n\n"
            f"I help you track expenses and build smart money habits.\n\n"
            f"To get started, I'll register you with this WhatsApp number:\n"
            f"*+{phone}*\n\n"
            f"Reply *YES* to confirm.",
        )
        if message_id:
            await _mark_processed_message(message_id)

        return {"status": "pending_confirmation", "phone": phone}
    except Exception:
        # Explicit rollback IS needed here because we catch the exception and
        # return a normal JSON response.  Without this, get_db() would try to
        # auto-commit a session in a broken/dirty state.
        await db.rollback()
        logger.exception("Error while processing WhatsApp webhook")
        return {"status": "error", "reason": "processing_failed"}


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

