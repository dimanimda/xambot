"""MAX Messenger adapter for platform-api.max.ru."""

from src.adapters.maxx.client import MaxRESTClient
from src.adapters.maxx.formatting import MaxMessageFormatter
from src.adapters.maxx.schemas import (
    MaxButton,
    MaxCallback,
    MaxMessage,
    MaxSendRequest,
    MaxWebhookPayload,
)
from src.adapters.maxx.webhook import MaxWebhookHandler

__all__ = [
    "MaxRESTClient",
    "MaxWebhookHandler",
    "MaxMessageFormatter",
    "MaxWebhookPayload",
    "MaxMessage",
    "MaxCallback",
    "MaxSendRequest",
    "MaxButton",
]
