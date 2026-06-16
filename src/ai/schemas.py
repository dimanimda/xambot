"""Pydantic schemas for AI provider request/response normalization."""

from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# Core normalized schemas — used by routers & adapters
# ============================================================


class MessageRecord(BaseModel):
    """Internal normalized message for conversation history."""

    role: str  # user | assistant | tool | system
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class FunctionCall(BaseModel):
    """A single function call from the AI."""

    call_id: str
    name: str
    arguments: dict[str, Any]


class UsageStats(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class AIResponse(BaseModel):
    """Normalized AI response — what the router works with."""

    response_id: str
    text: str | None = None
    function_calls: list[FunctionCall] | None = None
    finish_reason: str | None = None  # "stop" | "tool_calls" | "length" | "error"
    usage: UsageStats | None = None


# ============================================================
# YAIS Responses API models
# ============================================================


class YaisToolParameter(BaseModel):
    """JSON Schema for tool parameters."""

    type: str = "object"
    properties: dict[str, Any]
    required: list[str] | None = None


class YaisTool(BaseModel):
    """YAIS tool definition."""

    type: str = "function"
    name: str
    description: str
    parameters: YaisToolParameter


class YaisResponseOutput(BaseModel):
    """Single item in YAIS Responses API output[] array."""

    type: str  # reasoning | function_call | message
    call_id: str | None = None
    name: str | None = None
    arguments: str | None = None  # JSON string
    content: list[dict[str, Any]] | None = None
    role: str | None = None
    summary: list[dict[str, Any]] | None = None


class YaisResponsesApiResponse(BaseModel):
    """Full YAIS /v1/responses response."""

    id: str
    status: str  # completed | failed | in_progress
    output: list[dict[str, Any]] = []
    usage: dict[str, int] | None = None


class YaisChatCompletionsResponse(BaseModel):
    """Fallback /v1/chat/completions response."""

    id: str
    choices: list[dict[str, Any]]
    usage: dict[str, int] | None = None
