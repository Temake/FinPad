"""WhatsApp webhook routes - Phase 5 implementation."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Receive incoming WhatsApp messages from Evolution API."""
    # TODO: Phase 5 implementation
    return {"message": "Not yet implemented"}


@router.get("/webhook")
async def whatsapp_webhook_verify():
    """Webhook verification endpoint for Evolution API."""
    # TODO: Phase 5 implementation
    return {"message": "Not yet implemented"}
