"""MessageRouter — the main orchestrator for end-to-end dialog processing.

Flow:
    IncomingMessage → resolve tenant → find/create user & conversation →
    store user message → build history → call AI → process response →
    update conversation state → return response text.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from src.ai.base import AIProvider
from src.ai.schemas import AIResponse, FunctionCall, MessageRecord
from src.core.config import settings
from src.core.exceptions import AIProviderError, ToolExecutionError
from src.core.logging_config import get_logger
from src.core.services.conversation_service import ConversationService
from src.core.services.message_service import MessageService
from src.core.services.user_service import UserService
from src.core.tenant import TenantManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.adapters.base import IncomingMessage
    from src.core.models.company import Company
    from src.core.models.conversation import Conversation
    from src.core.models.user import User
    from src.plugins.registry import PluginRegistry

logger = get_logger(__name__)


class MessageRouter:
    """Orchestrates the full message processing pipeline.

    Responsibilities:
    1. Resolve tenant (company) from slug
    2. Find or create the user and conversation
    3. Persist the incoming message
    4. Build conversation history for AI context
    5. Load system prompt and tools for the company
    6. Call the AI provider (YAIS)
    7. Handle tool calls (function calls) if present (Week 2)
    8. Store AI response and update conversation state
    9. Return the response text

    Usage::

        router = MessageRouter(db, ai_provider, plugin_registry)
        response_text = await router.process_message(incoming)
    """

    # ── Configuration ───────────────────────────────────────────────

    MAX_TOOL_ITERATIONS: int = 5
    HISTORY_LIMIT: int = 20

    # ── Initialisation ──────────────────────────────────────────────

    def __init__(
        self,
        db: "AsyncSession",
        ai_provider: AIProvider,
        plugin_registry: "PluginRegistry | None" = None,
    ) -> None:
        self._db = db
        self._ai = ai_provider
        self._plugin_registry = plugin_registry

        # Services (share the same DB session)
        self._tenant_mgr = TenantManager(db)
        self._user_service = UserService(db)
        self._conv_service = ConversationService(db)
        self._msg_service = MessageService(db)

    # ── Public API ──────────────────────────────────────────────────

    async def process_message(self, incoming: "IncomingMessage") -> str:
        """Process an incoming message end-to-end.

        Args:
            incoming: Normalised incoming message from any messenger.

        Returns:
            Response text to send back to the user.
        """
        start_time = time.monotonic()

        # --- Step 1: Resolve tenant ---
        company = await self._tenant_mgr.get_by_slug(incoming.company_slug)
        logger.info(
            "Tenant resolved",
            company_slug=company.slug,
            company_name=company.name,
        )

        # --- Step 2: Find or create user ---
        user = await self._user_service.get_or_create(
            company_id=company.id,
            messenger=incoming.messenger,
            messenger_user_id=incoming.messenger_user_id,
        )

        # --- Step 3: Find or create conversation ---
        conversation = await self._conv_service.get_or_create_active(
            company_id=company.id,
            user_id=user.id,
            messenger=incoming.messenger,
            messenger_chat_id=incoming.messenger_chat_id,
        )

        # --- Step 4: Store user message ---
        await self._msg_service.create(
            conversation_id=conversation.id,
            role="user",
            content=incoming.text or "",
        )

        # --- Step 5: Build conversation history ---
        history = await self._msg_service.get_conversation_history(
            conversation.id,
            limit=self.HISTORY_LIMIT,
        )
        message_records = self._messages_to_records(history)

        # --- Step 6: Load system prompt ---
        system_prompt = self._build_system_prompt(company)

        # --- Step 7: Get tools for company ---
        tools = self._get_tools(company.id)  # Week 1: empty list

        # --- Step 8: Call AI ---
        try:
            ai_response = await self._ai.chat(
                instructions=system_prompt,
                input_text=incoming.text or "",
                tools=tools,
                messages_history=message_records,
                previous_response_id=conversation.previous_response_id,
            )
        except AIProviderError as exc:
            logger.error(
                "AI provider error",
                error=str(exc),
                company_slug=company.slug,
            )
            return (
                "Извините, произошла ошибка при обработке запроса. "
                "Пожалуйста, попробуйте позже."
            )

        # --- Step 9: Process AI response (may loop for tool calls) ---
        response_text = await self._process_ai_response(
            ai_response=ai_response,
            conversation=conversation,
            company=company,
            user=user,
            tools=tools,
            iteration=0,
        )

        # --- Step 10: Update conversation state ---
        await self._conv_service.update_previous_response_id(
            conversation.id, ai_response.response_id
        )
        await self._conv_service.touch_last_message(conversation.id)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Message processed",
            company_slug=company.slug,
            conversation_id=str(conversation.id),
            response_id=ai_response.response_id,
            has_text=response_text is not None,
            has_function_calls=ai_response.function_calls is not None,
            elapsed_ms=elapsed_ms,
        )

        return response_text or ""

    # ── Response handling ───────────────────────────────────────────

    async def _process_ai_response(
        self,
        ai_response: AIResponse,
        conversation: "Conversation",
        company: "Company",
        user: "User",
        tools: list[dict] | None,
        iteration: int,
    ) -> str | None:
        """Process the AI response: handle function calls or return text.

        If the AI requests function calls:
            1. Store the assistant message with tool_calls metadata.
            2. Execute each function call via the plugin registry.
            3. Store tool results as messages.
            4. Submit results back to the AI and loop (up to MAX_TOOL_ITERATIONS).

        If the AI returns text:
            1. Store the assistant message.
            2. Return the text.

        Week 1: tool calls will return placeholder errors.
        """
        if (
            ai_response.function_calls
            and iteration < self.MAX_TOOL_ITERATIONS
        ):
            logger.info(
                "AI requested function calls",
                calls=[fc.name for fc in ai_response.function_calls],
                iteration=iteration,
            )

            # Store assistant message with function calls metadata
            await self._msg_service.create(
                conversation_id=conversation.id,
                role="assistant",
                content=None,
                tool_calls=[
                    {"call_id": fc.call_id, "name": fc.name, "arguments": fc.arguments}
                    for fc in ai_response.function_calls
                ],
                metadata={
                    "response_id": ai_response.response_id,
                    "usage": ai_response.usage.model_dump() if ai_response.usage else None,
                },
            )

            # Execute each tool call and collect results
            tool_results: dict[str, str] = {}
            for fc in ai_response.function_calls:
                tool_result = await self._execute_tool(
                    fc=fc,
                    company_id=company.id,
                    user_id=user.id,
                )
                tool_results[fc.call_id] = tool_result
                # Store tool result
                await self._msg_service.create(
                    conversation_id=conversation.id,
                    role="tool",
                    content=tool_result,
                    tool_call_id=fc.call_id,
                    metadata={"tool_name": fc.name},
                )

            # Submit first tool result back to AI to continue
            first_call = ai_response.function_calls[0]
            first_result = tool_results[first_call.call_id]

            try:
                next_response = await self._ai.submit_tool_result(
                    previous_response_id=ai_response.response_id,
                    call_id=first_call.call_id,
                    tool_name=first_call.name,
                    result_json=first_result,
                    tools=tools,
                )
            except AIProviderError as exc:
                logger.error(
                    "AI error during tool result submission",
                    error=str(exc),
                    tool_name=first_call.name,
                )
                return (
                    "Не удалось выполнить запрошенное действие. "
                    "Пожалуйста, попробуйте позже."
                )

            # Recurse
            return await self._process_ai_response(
                ai_response=next_response,
                conversation=conversation,
                company=company,
                user=user,
                tools=tools,
                iteration=iteration + 1,
            )

        if iteration >= self.MAX_TOOL_ITERATIONS:
            logger.warning(
                "Max tool call iterations reached",
                max_iterations=self.MAX_TOOL_ITERATIONS,
                conversation_id=str(conversation.id),
            )
            return (
                "Достигнут лимит операций. "
                "Пожалуйста, упростите запрос или попробуйте позже."
            )

        # --- Handle text response ---
        text = ai_response.text

        if text:
            # Store assistant message
            metadata: dict = {"response_id": ai_response.response_id}
            if ai_response.usage:
                metadata["usage"] = ai_response.usage.model_dump()
            metadata["model"] = ai_response.response_id  # approximate

            await self._msg_service.create(
                conversation_id=conversation.id,
                role="assistant",
                content=text,
                metadata=metadata,
            )
            return text

        # Edge case: no text and no function calls
        logger.warning(
            "AI returned empty response (no text, no function calls)",
            response_id=ai_response.response_id,
            finish_reason=ai_response.finish_reason,
        )
        return "Я не смог сформулировать ответ. Пожалуйста, переформулируйте запрос."

    # ── Tool execution ──────────────────────────────────────────────

    async def _execute_tool(
        self,
        fc: FunctionCall,
        company_id,
        user_id,
    ) -> str:
        """Execute a single tool call via the plugin registry.

        Week 1: returns a placeholder error (plugin system not built yet).
        Week 2: dispatches to the registered plugin.
        """
        if self._plugin_registry is None:
            return json.dumps(
                {
                    "error": "Plugin system is not available",
                    "tool": fc.name,
                    "message": "Интеграции будут доступны на следующей неделе.",
                },
                ensure_ascii=False,
            )

        try:
            result = await self._plugin_registry.execute_tool(
                tool_name=fc.name,
                arguments=fc.arguments,
                context={
                    "company_id": str(company_id),
                    "user_id": str(user_id),
                },
            )
            return json.dumps(result, ensure_ascii=False)
        except ToolExecutionError as exc:
            logger.error(
                "Tool execution failed",
                tool_name=fc.name,
                error=str(exc),
            )
            return json.dumps({"error": str(exc), "tool": fc.name}, ensure_ascii=False)

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _messages_to_records(
        messages: list,
    ) -> list[MessageRecord]:
        """Convert DB Message objects to MessageRecord for the AI provider."""
        return [
            MessageRecord(
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls,
                tool_call_id=msg.tool_call_id,
                name=(
                    msg.metadata_.get("tool_name")
                    if msg.metadata_ and msg.role == "tool"
                    else None
                ),
            )
            for msg in messages
        ]

    @staticmethod
    def _build_system_prompt(company: "Company") -> str:
        """Build the system prompt for the AI from company settings.

        Falls back to a sensible default if no custom prompt is configured.
        """
        custom_prompt = (
            company.settings.get("system_prompt", "")
            if company.settings
            else ""
        )
        if custom_prompt:
            return custom_prompt

        return (
            f"Ты — AI-ассистент компании «{company.name}». "
            "Отвечай на русском языке. "
            "Будь вежлив и профессионален. "
            "Если тебя просят выполнить действие (создать лида, найти сделку), "
            "сообщи, что эта функция будет доступна позже."
        )

    def _get_tools(self, company_id) -> list[dict] | None:
        """Get registered tools for the company.

        Week 1: returns ``None`` (no plugins loaded).
        Week 2: returns tools from plugin manifests.

        Returns ``None`` (not ``[]``) to signal the AI not to use tools.
        """
        if self._plugin_registry is None:
            return None
        # PluginRegistry.get_tools_for_ai() is synchronous in Week 1 stub
        return self._plugin_registry.get_tools_for_ai(company_id)
