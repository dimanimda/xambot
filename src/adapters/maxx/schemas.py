"""Pydantic models for MAX Messenger API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# MAX Webhook Payload Models (incoming via webhook)
# ============================================================


class MaxWebhookChat(BaseModel):
    """Chat info from webhook object."""

    chat_id: str


class MaxWebhookFrom(BaseModel):
    """Sender info from webhook object."""

    user_id: str


class MaxWebhookUser(BaseModel):
    """User info (used in callback objects)."""

    user_id: str


class MaxWebhookMessage(BaseModel):
    """Message object within a webhook callback."""

    chat: MaxWebhookChat


class MaxWebhookMessageObject(BaseModel):
    """The 'object' field when type='message_new'."""

    message_id: int | str
    chat: MaxWebhookChat
    from_: MaxWebhookFrom = Field(alias="from")
    text: str | None = None
    timestamp: int | None = None


class MaxWebhookCallbackObject(BaseModel):
    """The 'object' field when type='callback'."""

    callback_id: str
    user: MaxWebhookUser
    message: MaxWebhookMessage
    payload: str = ""


class MaxWebhookPayload(BaseModel):
    """Root webhook payload from MAX platform.

    Two main event types:
    - "message_new": new incoming message
    - "callback": inline keyboard button press

    Examples:
        Message:
        {
            "update_id": 1,
            "type": "message_new",
            "object": {
                "message_id": 456,
                "chat": {"chat_id": 789},
                "from": {"user_id": "123"},
                "text": "Привет!"
            }
        }

        Callback:
        {
            "update_id": 2,
            "type": "callback",
            "object": {
                "callback_id": "cb_1",
                "user": {"user_id": "123"},
                "message": {"chat": {"chat_id": 789}},
                "payload": "action_1"
            }
        }
    """

    update_id: int
    type: str  # "message_new" | "callback" | ...
    object: dict[str, Any]  # Raw dict — parsed manually by handler


# ============================================================
# MAX Domain Models (normalised)
# ============================================================


class MaxMessage(BaseModel):
    """Normalised MAX message representation."""

    message_id: int | str
    chat_id: str
    user_id: str
    text: str | None = None
    timestamp: int | None = None


class MaxCallback(BaseModel):
    """Normalised MAX callback (inline button press)."""

    callback_id: str
    user_id: str
    payload: str
    chat_id: str


# ============================================================
# MAX Send / Request Models
# ============================================================


class MaxButton(BaseModel):
    """Inline keyboard button definition.

    Example:
        MaxButton(type="callback", text="Click me", payload="action_1")
    """

    type: str = "callback"  # "callback" | "url"
    text: str
    payload: str  # callback data (or URL when type="url")


class MaxInlineKeyboardPayload(BaseModel):
    """Payload for inline_keyboard attachment."""

    buttons: list[list[MaxButton]]


class MaxInlineKeyboardAttachment(BaseModel):
    """Attachment structure for inline_keyboard."""

    type: str = "inline_keyboard"
    payload: MaxInlineKeyboardPayload


class MaxSendRequest(BaseModel):
    """Request body for POST /messages.

    Example:
        {
            "chat_id": "123",
            "text": "Hello *bold*",
            "format": "markdown",
            "attachments": [{
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [[
                        {"type": "callback", "text": "Btn 1", "payload": "a1"},
                        {"type": "callback", "text": "Btn 2", "payload": "a2"}
                    ]]
                }
            }]
        }
    """

    chat_id: str
    text: str
    format: str | None = None  # "markdown" | "html" | None (plain text)
    attachments: list[dict[str, Any]] | None = None
