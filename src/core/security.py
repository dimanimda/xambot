"""Fernet-based symmetric encryption for API keys at rest.

Uses AES-128-CBC + HMAC through cryptography.fernet.
Encrypts dict → base64 string. Decrypts base64 string → dict.
"""

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """Symmetric encryption service using Fernet (AES-128-CBC + HMAC)."""

    def __init__(self, key: bytes) -> None:
        """Initialize with a 32-byte url-safe base64-encoded Fernet key."""
        self._fernet = Fernet(key)

    def encrypt(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary to a base64-encoded string.

        >>> svc.encrypt({"webhook_url": "https://..."})
        'gAAAAAB...'
        """
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        token = self._fernet.encrypt(json_bytes)
        return token.decode("utf-8")

    def decrypt(self, token: str) -> dict[str, Any]:
        """Decrypt a base64-encoded string back to a dictionary.

        Raises ValueError if the token is invalid or has been tampered with.
        """
        try:
            json_bytes = self._fernet.decrypt(token.encode("utf-8"))
            return json.loads(json_bytes)
        except (InvalidToken, json.JSONDecodeError) as e:
            raise ValueError("Invalid or corrupted encrypted token") from e

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet key."""
        return Fernet.generate_key()
