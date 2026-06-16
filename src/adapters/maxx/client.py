"""REST client for MAX Messenger Bot API (platform-api.max.ru)."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

from src.adapters.maxx.schemas import MaxButton, MaxInlineKeyboardAttachment, MaxInlineKeyboardPayload
from src.core.exceptions import MaxAPIError, MessengerError, MessengerSendError

logger = structlog.get_logger(__name__)


class MaxRESTClient:
    """Async REST client for MAX Bot API.

    Authentication: ``Authorization: {bot_token}`` header (plain token, NOT Bearer).
    Base URL: ``https://platform-api.max.ru``.
    Rate limit: 30 requests per second.

    Usage::

        client = MaxRESTClient(bot_token="abc123")
        await client.send_message("chat_1", "Hello!")
        await client.close()
    """

    _MAX_RPS = 30

    def __init__(
        self,
        bot_token: str,
        base_url: str = "https://platform-api.max.ru",
        httpx_client: httpx.AsyncClient | None = None,
        timeout: int = 10,
    ) -> None:
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx_client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": bot_token,
                "Content-Type": "application/json",
            },
        )
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send_message(
        self,
        chat_id: str,
        text: str,
        format: str | None = None,
        buttons: list[MaxButton] | None = None,
    ) -> dict[str, Any]:
        """Send a message to a MAX chat.

        Args:
            chat_id: Target chat ID.
            text: Message text. May contain Markdown/HTML markup.
            format: ``"markdown"``, ``"html"``, or ``None`` (plain text).
            buttons: Inline keyboard buttons (arranged in 2 columns by the API
                call itself — the caller is responsible for grouping into rows).

        Returns:
            API response dict (contains ``message_id`` etc.).
        """
        attachments: list[dict[str, Any]] | None = None
        if buttons:
            # Group buttons into rows of 2
            rows: list[list[MaxButton]] = []
            for i in range(0, len(buttons), 2):
                rows.append(buttons[i : i + 2])

            keyboard = MaxInlineKeyboardAttachment(
                payload=MaxInlineKeyboardPayload(buttons=rows)
            )
            attachments = [keyboard.model_dump(exclude_none=True)]

        body: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if format is not None:
            body["format"] = format
        if attachments is not None:
            body["attachments"] = attachments

        return await self._request("POST", "/messages", body)

    async def get_file(self, file_id: str) -> bytes:
        """Download a file from MAX.

        Args:
            file_id: MAX file ID.

        Returns:
            Raw file bytes.
        """
        url = f"{self.base_url}/files/{file_id}"
        await self._check_rate_limit()
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc.response.status_code, exc.response.json())
            raise  # unreachable
        except httpx.RequestError as exc:
            logger.error("Network error fetching file", file_id=file_id, error=str(exc))
            raise MaxAPIError(f"Failed to fetch file {file_id}: {exc}") from exc

    async def get_me(self) -> dict[str, Any]:
        """Get bot information (identity and capabilities).

        Endpoint: ``GET /me``.

        Returns:
            Bot info dict.
        """
        return await self._request("GET", "/me")

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an HTTP request to the MAX API with rate limiting and error handling.

        Headers are set on the client instance:
            - ``Authorization: {bot_token}``
            - ``Content-Type: application/json``
        """
        url = f"{self.base_url}{path}"
        await self._check_rate_limit()

        logger.debug(
            "MAX API request",
            method=method,
            path=path,
            chat_id=json_data.get("chat_id") if json_data else None,
        )

        try:
            response = await self._client.request(method, url, json=json_data)
            response.raise_for_status()
            data = response.json()
            logger.debug("MAX API response", method=method, path=path, status=response.status_code)
            return data
        except httpx.HTTPStatusError as exc:
            try:
                error_body = exc.response.json()
            except Exception:
                error_body = {"description": exc.response.text}
            self._handle_http_error(exc.response.status_code, error_body)
            raise  # unreachable — _handle_http_error always raises
        except httpx.RequestError as exc:
            logger.error("Network error calling MAX API", method=method, path=path, error=str(exc))
            raise MessengerSendError(f"Network error: {exc}") from exc

    def _handle_http_error(self, status_code: int, body: dict[str, Any]) -> None:
        """Map HTTP errors to our exception hierarchy.

        Always raises — never returns normally.
        """
        description = body.get("description", body.get("message", str(body)))

        if status_code == 400:
            raise MaxAPIError(f"Bad request: {description}", status_code=status_code)
        if status_code in (401, 403):
            raise MaxAPIError(f"Authentication failed: {description}", status_code=status_code)
        if status_code == 429:
            raise MaxAPIError("Rate limit exceeded", status_code=status_code)
        if status_code >= 500:
            raise MessengerSendError(f"MAX server error {status_code}: {description}")

        raise MessengerError(f"Unexpected MAX API error {status_code}: {description}")

    async def _check_rate_limit(self) -> None:
        """Enforce 30 RPS rate limit using a sliding window."""
        now = time.monotonic()
        async with self._lock:
            # Remove timestamps older than 1 second
            self._request_times = [t for t in self._request_times if now - t < 1.0]

            if len(self._request_times) >= self._MAX_RPS:
                # Wait until the oldest request falls outside the window
                sleep_time = 1.0 - (now - self._request_times[0]) + 0.01
                if sleep_time > 0:
                    logger.debug("Rate limit wait", sleep_seconds=round(sleep_time, 3))
                    await asyncio.sleep(sleep_time)
                now = time.monotonic()
                self._request_times = [t for t in self._request_times if now - t < 1.0]

            self._request_times.append(now)
