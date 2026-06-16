"""Webhook endpoints for messenger platforms.

MAX Messenger webhook:
    POST /api/v1/webhooks/maxx/{company_slug}

Future: Telegram, VK, etc.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.maxx.client import MaxRESTClient
from src.adapters.maxx.webhook import MaxWebhookHandler
from src.core.config import settings as global_settings
from src.core.database import get_session
from src.core.exceptions import (
    CompanyNotFoundError,
    MaxAPIError,
    MessengerSendError,
    TenantInactiveError,
)
from src.core.logging_config import get_logger
from src.core.router import MessageRouter
from src.core.security import EncryptionService
from src.core.services.integration_service import IntegrationService

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
logger = get_logger(__name__)


@router.post("/maxx/{company_slug}")
async def maxx_webhook(
    company_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Handle incoming MAX Messenger webhook.

    MAX sends message updates to this endpoint.
    The URL pattern ``/api/v1/webhooks/maxx/{company_slug}``
    allows multi-tenant routing: each company has its own webhook URL.

    Flow:
        1. Parse the JSON payload.
        2. Resolve the MAX bot token for this company.
        3. Parse the payload into a normalised ``IncomingMessage``.
        4. Route through ``MessageRouter`` to get an AI response.
        5. Send the response back to MAX via REST API.
        6. Always return HTTP 200 to prevent MAX from retrying.

    Returns:
        ``{"status": "ok"}`` on success,
        ``{"status": "error", "detail": "..."}`` on processing errors,
        HTTP 404 if the company slug is unknown.
    """
    # --- Step 1: Parse payload ---
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Failed to parse webhook JSON body", company_slug=company_slug)
        return {"status": "error", "detail": "Invalid JSON payload"}

    logger.info(
        "MAX webhook received",
        company_slug=company_slug,
        update_id=payload.get("update_id"),
        event_type=payload.get("type"),
    )

    # --- Step 2: Resolve bot token and webhook secret ---
    bot_token, webhook_secret = await _resolve_bot_token_and_secret(
        db=db,
        company_slug=company_slug,
        app_state=request.app.state,
    )
    if not bot_token:
        logger.error(
            "MAX bot token not configured",
            company_slug=company_slug,
        )
        return {"status": "error", "detail": "MAX bot token not configured"}

    # --- Step 3: Verify webhook signature ---
    handler = MaxWebhookHandler()
    if not handler.verify_webhook(payload, webhook_secret):
        logger.warning(
            "Webhook signature verification failed",
            company_slug=company_slug,
        )
        return {"status": "error", "detail": "Invalid webhook signature"}

    # --- Step 4: Parse incoming message ---
    try:
        incoming = handler.parse_incoming(payload)
        incoming.company_slug = company_slug
    except (ValueError, KeyError) as exc:
        logger.warning(
            "Failed to parse MAX webhook payload",
            error=str(exc),
            company_slug=company_slug,
        )
        return {"status": "error", "detail": f"Unrecognised payload: {exc}"}

    # --- Step 4: Route through MessageRouter ---
    ai_provider = request.app.state.ai_provider
    plugin_registry = getattr(request.app.state, "plugin_registry", None)

    router_instance = MessageRouter(
        db=db,
        ai_provider=ai_provider,
        plugin_registry=plugin_registry,
    )

    try:
        response_text = await router_instance.process_message(incoming)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_slug}' not found",
        )
    except TenantInactiveError as exc:
        logger.warning("Company is inactive", company_slug=company_slug)
        return {"status": "error", "detail": str(exc)}
    except Exception as exc:
        logger.error(
            "Unexpected error in message processing",
            error=str(exc),
            company_slug=company_slug,
            exc_info=True,
        )
        return {"status": "error", "detail": "Internal processing error"}

    # --- Step 5: Send response back to MAX ---
    if response_text:
        max_client = MaxRESTClient(bot_token=bot_token)
        try:
            await max_client.send_message(
                chat_id=incoming.messenger_chat_id,
                text=response_text,
                format="markdown",
            )
        except (MaxAPIError, MessengerSendError) as exc:
            logger.error(
                "Failed to send message to MAX",
                error=str(exc),
                chat_id=incoming.messenger_chat_id,
            )
            # Don't crash — the message is already stored in DB.
            return {"status": "ok", "warning": "Response stored but send failed"}
        finally:
            await max_client.close()

    # --- Step 6: Commit DB transaction ---
    await db.commit()

    return {"status": "ok"}


# ── Helpers ─────────────────────────────────────────────────────────


async def _resolve_bot_token_and_secret(
    db: AsyncSession,
    company_slug: str,
    app_state,
) -> tuple[str | None, str]:
    """Resolve the MAX bot token and webhook secret for a given company.

    Resolution order:
        1. Look up the ``maxx`` integration in the DB for this company
           (encrypted config).  Uses the company_id resolved from slug.
        2. Fall back to ``MULTIBOT_MAX_DEFAULT_BOT_TOKEN`` from settings.

    Returns:
        Tuple of ``(bot_token, webhook_secret)``.  ``bot_token`` may be None,
        ``webhook_secret`` defaults to ``""``.
    """
    # Try per-company integration first
    from src.core.services.company_service import CompanyService

    company_svc = CompanyService(db)
    company = await company_svc.get_by_slug(company_slug)

    webhook_secret = ""
    if company is not None:
        encryption_key = global_settings.get_encryption_key()
        encryption_svc = EncryptionService(encryption_key)
        integration_svc = IntegrationService(db, encryption_svc)
        max_config = await integration_svc.get_raw_config(company.id, "maxx")
        if max_config:
            if max_config.get("bot_token"):
                return max_config["bot_token"], max_config.get("webhook_secret", "")
            webhook_secret = max_config.get("webhook_secret", "")

    # Fall back to global default
    return global_settings.max_default_bot_token or None, webhook_secret
