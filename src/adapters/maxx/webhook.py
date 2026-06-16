"""MAX Messenger webhook handler — parses incoming payloads."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import structlog

from src.adapters.base import IncomingMessage

logger = structlog.get_logger(__name__)


class MaxWebhookHandler:
    """Handles incoming MAX webhook payloads.

    Normalises MAX-specific payload structures into the platform's
    :class:`~src.adapters.base.IncomingMessage` format.

    Supports two event types:
    - ``message_new`` — new text message from user
    - ``callback`` — inline keyboard button press

    Usage::

        handler = MaxWebhookHandler()
        incoming = handler.parse_incoming(raw_payload)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_incoming(self, payload: dict[str, Any]) -> IncomingMessage:
        """Parse a raw MAX webhook payload into a normalised IncomingMessage.

        Args:
            payload: Raw JSON dict from MAX webhook request body.

        Returns:
            Normalised incoming message ready for routing.

        Raises:
            ValueError: If payload structure is unrecognised.
        """
        event_type = payload.get("type", "")
        obj = payload.get("object", {})

        if event_type == "message_new":
            return self._parse_message_new(obj)
        elif event_type == "callback":
            return self._parse_callback(obj)
        else:
            logger.warning("Unknown MAX webhook event type", type=event_type, payload=payload)
            raise ValueError(f"Unknown webhook event type: {event_type}")

    @staticmethod
    def verify_webhook(payload: dict[str, Any], secret: str) -> bool:
        """Verify webhook request authenticity via HMAC signature check.

        Checks the ``X-Signature`` header (if present) against an HMAC-SHA256
        of the raw request body using the shared secret.

        Args:
            payload: The webhook payload dict.
            secret: Shared secret for HMAC.

        Returns:
            ``True`` if the signature is valid or not present (passthrough).
        """
        signature_header = payload.pop("_signature", "") if isinstance(payload, dict) else ""

        if not signature_header or not secret:
            # No signature provided → pass through (MAX may add signatures later)
            return True

        # Re-encode payload to canonical JSON bytes for HMAC
        import json

        raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(expected, signature_header)

    # ------------------------------------------------------------------
    # Private parsers
    # ------------------------------------------------------------------

    def _parse_message_new(self, obj: dict[str, Any]) -> IncomingMessage:
        """Parse a ``message_new`` event object.

        Expected ``obj`` structure::

            {
                "message_id": 456,
                "chat": {"chat_id": 789},
                "from": {"user_id": "123"},
                "text": "Привет!"
            }
        """
        messenger_user_id = str(obj.get("from", {}).get("user_id", ""))
        messenger_chat_id = str(obj.get("chat", {}).get("chat_id", ""))
        text = obj.get("text", "")

        logger.debug(
            "Parsed message_new",
            user_id=messenger_user_id,
            chat_id=messenger_chat_id,
            text_preview=text[:100] if text else "",
        )

        return IncomingMessage(
            messenger="maxx",
            messenger_user_id=messenger_user_id,
            messenger_chat_id=messenger_chat_id,
            text=text,
        )

    def _parse_callback(self, obj: dict[str, Any]) -> IncomingMessage:
        """Parse a ``callback`` event object (inline button press).

        Expected ``obj`` structure::

            {
                "callback_id": "cb_1",
                "user": {"user_id": "123"},
                "message": {"chat": {"chat_id": 789}},
                "payload": "action_1"
            }
        """
        messenger_user_id = str(obj.get("user", {}).get("user_id", ""))
        messenger_chat_id = str(obj.get("message", {}).get("chat", {}).get("chat_id", ""))
        payload_data = obj.get("payload", "")

        logger.debug(
            "Parsed callback",
            user_id=messenger_user_id,
            chat_id=messenger_chat_id,
            callback_payload=payload_data,
        )

        return IncomingMessage(
            messenger="maxx",
            messenger_user_id=messenger_user_id,
            messenger_chat_id=messenger_chat_id,
            text=payload_data,  # callback payload becomes the "text" for routing
        )
