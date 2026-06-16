"""Application settings loaded from environment variables.

All variables use the MULTIBOT_ prefix.
"""

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict

import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """MultiBot configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_prefix="MULTIBOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Application ----
    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    webhook_base_url: str = ""

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://multibot:multibot@localhost:5432/multibot"

    # ---- Encryption ----
    encryption_key: str = ""

    # ---- Yandex AI Studio (YAIS) ----
    yais_api_key: str = ""
    yais_folder_id: str = ""
    yais_base_url: str = "https://ai.api.yandexcloud.net"
    yais_primary_model: str = ""
    yais_fallback_model: str = "yandexgpt-5-lite"
    yais_embedding_model: str = "text-embeddings-v2"

    # ---- MAX Messenger ----
    max_default_bot_token: str = ""

    # ---- Limits & Timeouts ----
    conversation_history_limit: int = 20
    tool_call_max_iterations: int = 5
    ai_request_timeout_seconds: int = 30
    messenger_send_timeout_seconds: int = 10

    def get_encryption_key(self) -> bytes:
        """Return the Fernet encryption key.

        If no key is configured, generate a temporary one and warn.
        In production, MULTIBOT_ENCRYPTION_KEY must be set explicitly.
        """
        if not self.encryption_key:
            key = Fernet.generate_key()
            logger.warning(
                "MULTIBOT_ENCRYPTION_KEY not set. Generated temporary key. "
                "Set MULTIBOT_ENCRYPTION_KEY in production!"
            )
            self.encryption_key = key.decode("utf-8")
        if isinstance(self.encryption_key, str):
            return self.encryption_key.encode("utf-8")
        return self.encryption_key

    def get_yais_model_url(self) -> str:
        """Return the primary YAIS model URL with folder_id substituted."""
        return self.yais_primary_model.format(folder=self.yais_folder_id)

    def get_yais_fallback_model_url(self) -> str:
        """Return the fallback YAIS model name."""
        return self.yais_fallback_model


settings = Settings()
