"""WhatsApp webhook routes - handles incoming messages from Evolution API."""

import logging

from fastapi import APIRouter, Request

from app.api.deps import DbSession
from app.services.user_service import get_user_by_phone, get_or_create_user
from app.services.whatsapp_service import WhatsAppService

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
        # User is registered — handle commands (Phase 5 will expand)
        if message_text.lower() in ("hi", "hello", "hey", "start"):
            await whatsapp.send_text(
                phone,
                f"👋 Hey{' ' + existing_user.display_name if existing_user.display_name else ''}! "
                f"Ready to track your spending?\n\n"
                f"• Send \"Spent 2000 on food\" to log\n"
                f"• Send \"Summary\" to see spending\n"
                f"• Send \"Help\" for all commands",
            )
        elif message_text.lower() == "help":
            await whatsapp.send_text(
                phone,
                "📋 *FinPad Commands*\n\n"
                "• \"Spent [amount] on [description]\" — Log expense\n"
                "• \"Summary\" — Today's spending summary\n"
                "• \"Week\" — This week's summary\n"
                "• \"Month\" — This month's summary\n"
                "• \"Help\" — Show this menu",
            )
        else:
            # TODO: Phase 5 — parse expense messages, handle summaries
            await whatsapp.send_text(
                phone,
                "🚧 I'm still learning! Right now I can help with:\n"
                "• Send \"Help\" to see available commands",
            )

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
