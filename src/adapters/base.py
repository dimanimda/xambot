"""Abstract messenger adapter interface."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Normalized incoming message from any messenger."""

    messenger: str  # "maxx" | "telegram" | "vk"
    messenger_user_id: str
    messenger_chat_id: str
    text: str | None = None
    company_slug: str = ""
    raw_payload: dict = {}


class OutgoingMessage(BaseModel):
    """Message to be sent back to user."""

    text: str
    parse_mode: str = "markdown"  # markdown | html | text
    reply_markup: dict | None = None  # Inline keyboard


class MessengerAdapter(ABC):
    """Abstract messenger adapter.

    Implemented for each messenger (MAX, Telegram, VK, etc.).
    """

    @abstractmethod
    async def parse_incoming(self, payload: dict) -> IncomingMessage:
        """Parse raw webhook payload → IncomingMessage."""
        ...

    @abstractmethod
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "markdown",
        reply_markup: dict | None = None,
    ) -> dict:
        """Send message to user. Returns messenger response."""
        ...

    @abstractmethod
    async def register_webhook(self, webhook_url: str) -> dict:
        """Register webhook URL with messenger."""
        ...

    @abstractmethod
    async def unregister_webhook(self) -> bool:
        """Remove webhook registration."""
        ...

    @abstractmethod
    async def verify_webhook_signature(
        self, payload: dict, headers: dict
    ) -> bool:
        """Verify webhook request authenticity."""
        ...
