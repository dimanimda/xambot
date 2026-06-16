"""Yandex AI Studio (YAIS) AI provider.

Implements the AIProvider interface using the YAIS Responses API
(gpt://{folder_id}/gpt-oss-20b/latest) with automatic fallback to
YandexGPT-5-lite via the Chat Completions API on failure.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.ai.base import AIProvider
from src.ai.schemas import AIResponse, FunctionCall, MessageRecord, UsageStats
from src.core.config import settings
from src.core.exceptions import (
    AIAuthError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
)
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class YAISResponsesProvider(AIProvider):
    """Yandex AI Studio provider using the Responses API.

    Primary flow:
        POST /v1/responses with model=gpt://{folder_id}/gpt-oss-20b/latest

    Fallback flow (on 4xx/5xx):
        POST /v1/chat/completions with model=yandexgpt-5-lite

    Multi-turn conversations use ``previous_response_id`` to maintain
    state on the YAIS side.
    """

    RESPONSES_ENDPOINT = "/v1/responses"
    CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"
    EMBEDDINGS_ENDPOINT = "/v1/embeddings"

    DEFAULT_MAX_OUTPUT_TOKENS = 500
    DEFAULT_EMBEDDING_MODEL = "text-embeddings-v2"

    # ── Initialisation ──────────────────────────────────────────────

    def __init__(
        self,
        api_key: str | None = None,
        folder_id: str | None = None,
        base_url: str | None = None,
        primary_model: str | None = None,
        fallback_model: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create a YAIS provider instance.

        All parameters default to values from ``settings`` when omitted.
        """
        self._api_key = api_key or settings.yais_api_key
        self._folder_id = folder_id or settings.yais_folder_id
        self._base_url = (base_url or settings.yais_base_url).rstrip("/")
        self._primary_model = primary_model or (
            settings.yais_primary_model.format(folder=self._folder_id)
        )
        self._fallback_model = fallback_model or settings.yais_fallback_model
        self._embedding_model = settings.yais_embedding_model
        self._timeout = httpx.Timeout(settings.ai_request_timeout_seconds)

        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return (or lazily create) the shared httpx.AsyncClient."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._build_headers(),
            )
        return self._http_client

    async def close(self) -> None:
        """Close the internal HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    # ── Public API ──────────────────────────────────────────────────

    async def chat(
        self,
        instructions: str,
        input_text: str,
        tools: list[dict] | None = None,
        messages_history: list[MessageRecord] | None = None,
        previous_response_id: str | None = None,
    ) -> AIResponse:
        """Send a conversation turn to YAIS.

        Uses the Responses API by default; falls back to the Chat
        Completions API on transport or server errors.
        """
        request_body = self._build_request(
            instructions=instructions,
            input_text=input_text,
            tools=tools,
            messages_history=messages_history,
            previous_response_id=previous_response_id,
        )

        try:
            return await self._call_responses_api(request_body)
        except AIProviderError:
            logger.warning(
                "YAIS Responses API failed, falling back to Chat Completions",
                model=self._primary_model,
                fallback_model=self._fallback_model,
            )
            return await self._fallback_chat(instructions, input_text)

    async def submit_tool_result(
        self,
        previous_response_id: str,
        call_id: str,
        tool_name: str,
        result_json: str,
        tools: list[dict] | None = None,
    ) -> AIResponse:
        """Submit a tool execution result and continue the conversation."""
        request_body: dict[str, Any] = {
            "model": self._primary_model,
            "previous_response_id": previous_response_id,
            "input": [
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result_json,
                }
            ],
            "max_output_tokens": self.DEFAULT_MAX_OUTPUT_TOKENS,
        }
        if tools:
            request_body["tools"] = tools

        logger.info(
            "Submitting tool result",
            response_id=previous_response_id,
            call_id=call_id,
            tool_name=tool_name,
        )

        try:
            return await self._call_responses_api(request_body)
        except AIProviderError:
            logger.warning("Tool result submission failed, no fallback available")
            raise

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via the YAIS Embeddings API."""
        request_body: dict[str, Any] = {
            "model": self._embedding_model,
            "texts": texts,
        }

        client = await self._get_client()
        url = f"{self._base_url}{self.EMBEDDINGS_ENDPOINT}"

        logger.info("Embedding request", model=self._embedding_model, count=len(texts))

        try:
            response = await client.post(url, json=request_body)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AITimeoutError("Embedding request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc

        data = response.json()
        embeddings: list[list[float]] = [
            item["embedding"] for item in data.get("embeddings", [])
        ]
        logger.info("Embedding response received", count=len(embeddings))
        return embeddings

    # ── Request building ────────────────────────────────────────────

    def _build_request(
        self,
        instructions: str,
        input_text: str,
        tools: list[dict] | None = None,
        messages_history: list[MessageRecord] | None = None,
        previous_response_id: str | None = None,
    ) -> dict[str, Any]:
        """Construct the YAIS /v1/responses request payload."""
        input_payload = self._build_input_payload(input_text, messages_history)

        body: dict[str, Any] = {
            "model": self._primary_model,
            "instructions": instructions,
            "input": input_payload,
            "max_output_tokens": self.DEFAULT_MAX_OUTPUT_TOKENS,
        }

        if tools:
            body["tools"] = tools

        if previous_response_id:
            body["previous_response_id"] = previous_response_id

        return body

    @staticmethod
    def _build_input_payload(
        input_text: str,
        messages_history: list[MessageRecord] | None = None,
    ) -> str | list[dict[str, Any]]:
        """Build the ``input`` field for the Responses API.

        Returns a plain string when there is no history, or a list of
        message objects when conversation history is provided.
        """
        if not messages_history:
            return input_text

        input_messages: list[dict[str, Any]] = []
        for msg in messages_history:
            entry: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                entry["content"] = msg.content
            if msg.tool_calls is not None:
                entry["tool_calls"] = msg.tool_calls
            if msg.tool_call_id is not None:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name is not None:
                entry["name"] = msg.name
            input_messages.append(entry)

        input_messages.append({"role": "user", "content": input_text})
        return input_messages

    # ── Core API call ───────────────────────────────────────────────

    async def _call_responses_api(self, body: dict[str, Any]) -> AIResponse:
        """Execute a POST /v1/responses request and parse the result."""
        client = await self._get_client()
        url = f"{self._base_url}{self.RESPONSES_ENDPOINT}"

        logger.info(
            "YAIS Responses API request",
            model=body.get("model"),
            has_tools=bool(body.get("tools")),
            previous_response_id=body.get("previous_response_id"),
        )

        try:
            response = await client.post(url, json=body)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AITimeoutError("YAIS Responses API request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc

        data = response.json()
        logger.info(
            "YAIS Responses API response",
            response_id=data.get("id"),
            status=data.get("status"),
        )

        return self._parse_response(data)

    # ── Response parsing ────────────────────────────────────────────

    def _parse_response(self, data: dict[str, Any]) -> AIResponse:
        """Convert a raw YAIS /v1/responses JSON dict into an AIResponse."""
        response_id: str = data.get("id", "")
        output: list[dict[str, Any]] = data.get("output", [])
        usage_data: dict[str, int] = data.get("usage") or {}

        text: str | None = None
        function_calls: list[FunctionCall] | None = None

        for item in output:
            item_type = item.get("type")

            if item_type == "message":
                text = self._extract_message_text(item)
            elif item_type == "function_call":
                if function_calls is None:
                    function_calls = []
                function_calls.append(self._parse_function_call(item))

        finish_reason: str | None
        if function_calls:
            finish_reason = "tool_calls"
        elif data.get("status") == "completed":
            finish_reason = "stop"
        elif data.get("status") == "failed":
            finish_reason = "error"
        else:
            finish_reason = None

        usage = UsageStats(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        ) if usage_data else None

        return AIResponse(
            response_id=response_id,
            text=text,
            function_calls=function_calls,
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def _extract_message_text(item: dict[str, Any]) -> str | None:
        """Extract assistant text from a ``message`` output item."""
        content_blocks: list[dict[str, Any]] = item.get("content", [])
        for block in content_blocks:
            if block.get("type") == "output_text":
                return block.get("text")
        return None

    @staticmethod
    def _parse_function_call(item: dict[str, Any]) -> FunctionCall:
        """Parse a ``function_call`` output item into a FunctionCall."""
        call_id: str = item.get("call_id", "")
        name: str = item.get("name", "")
        arguments_str: str = item.get("arguments", "{}")

        try:
            arguments: dict[str, Any] = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        return FunctionCall(call_id=call_id, name=name, arguments=arguments)

    def _handle_function_calls(
        self, output: list[dict[str, Any]]
    ) -> list[FunctionCall]:
        """Extract all ``function_call`` items from the output array."""
        calls: list[FunctionCall] = []
        for item in output:
            if item.get("type") == "function_call":
                calls.append(self._parse_function_call(item))
        return calls

    # ── Fallback ────────────────────────────────────────────────────

    async def _fallback_chat(
        self, instructions: str, input_text: str
    ) -> AIResponse:
        """Fallback: use the Chat Completions API with YandexGPT-5-lite.

        This is called automatically when the primary Responses API fails
        with a 4xx or 5xx status code.
        """
        client = await self._get_client()
        url = f"{self._base_url}{self.CHAT_COMPLETIONS_ENDPOINT}"

        request_body: dict[str, Any] = {
            "model": self._fallback_model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "max_tokens": self.DEFAULT_MAX_OUTPUT_TOKENS,
        }

        logger.info(
            "YAIS fallback Chat Completions request",
            model=self._fallback_model,
        )

        try:
            response = await client.post(url, json=request_body)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AITimeoutError("YAIS Chat Completions fallback timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc

        data = response.json()
        response_id: str = data.get("id", "")
        choices: list[dict[str, Any]] = data.get("choices", [])
        usage_data: dict[str, int] = data.get("usage") or {}

        text: str | None = None
        if choices:
            message = choices[0].get("message", {})
            text = message.get("content")

        usage = UsageStats(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        ) if usage_data else None

        logger.info(
            "YAIS fallback response",
            response_id=response_id,
            has_text=text is not None,
        )

        return AIResponse(
            response_id=response_id,
            text=text,
            function_calls=None,
            finish_reason="stop" if text else "error",
            usage=usage,
        )

    # ── Helpers ─────────────────────────────────────────────────────

    def _build_headers(self) -> dict[str, str]:
        """Return HTTP headers required by the YAIS API."""
        return {
            "Authorization": f"Api-Key {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _map_http_error(exc: httpx.HTTPStatusError) -> AIProviderError:
        """Map an httpx HTTPStatusError to the appropriate AI error."""
        status_code = exc.response.status_code

        if status_code == 401 or status_code == 403:
            return AIAuthError(
                f"YAIS authentication failed (HTTP {status_code})",
                code="AI_AUTH_ERROR",
            )
        if status_code == 429:
            return AIRateLimitError(
                "YAIS rate limit exceeded",
                code="AI_RATE_LIMIT",
            )

        # Try to extract an error message from the response body.
        detail = f"HTTP {status_code}"
        try:
            body = exc.response.json()
            error_msg = body.get("error", {}).get("message", body.get("message", ""))
            if error_msg:
                detail = error_msg
        except Exception:
            detail = exc.response.text[:200]

        return AIProviderError(
            f"YAIS API error: {detail}",
            code="AI_PROVIDER_ERROR",
        )
