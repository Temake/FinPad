"""OTP delivery service - tries WhatsApp first, falls back to SMS."""

from app.services.whatsapp_service import WhatsAppService
from app.services.sms_service import TermiiService


async def deliver_otp(phone: str, otp: str) -> dict:
    """
    Send OTP to user. Tries WhatsApp (free) first, falls back to SMS (paid).

    Returns: {"method": "whatsapp"|"sms"|None, "success": bool}
    """
    # Attempt 1: WhatsApp via Evolution API (FREE)
    whatsapp = WhatsAppService()
    whatsapp_sent = await whatsapp.send_otp(phone, otp)

    if whatsapp_sent:
        return {"method": "whatsapp", "success": True}

    # Attempt 2: SMS via Termii (PAID ~₦4/message)
    sms = TermiiService()
    sms_sent = await sms.send_otp(phone, otp)

    if sms_sent:
        return {"method": "sms", "success": True}

    # Both failed — in dev mode without services, return for testing
    return {"method": None, "success": False}
