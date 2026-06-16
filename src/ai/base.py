"""Abstract AI provider interface."""

from abc import ABC, abstractmethod

from src.ai.schemas import AIResponse, MessageRecord


class AIProvider(ABC):
    """Abstract AI provider interface.

    All AI providers (YAIS, OpenAI, local models) implement this interface.
    """

    @abstractmethod
    async def chat(
        self,
        instructions: str,
        input_text: str,
        tools: list[dict] | None = None,
        messages_history: list[MessageRecord] | None = None,
        previous_response_id: str | None = None,
    ) -> AIResponse:
        """Send a conversation turn to the AI and get a response.

        Args:
            instructions: System-level instructions for the AI.
            input_text: The current user message text.
            tools: Optional list of tool/function definitions in YAIS format.
            messages_history: Previous conversation turns.
            previous_response_id: For multi-turn stateful conversations.

        Returns:
            AIResponse with text and/or function_calls.
        """
        ...

    @abstractmethod
    async def submit_tool_result(
        self,
        previous_response_id: str,
        call_id: str,
        tool_name: str,
        result_json: str,
        tools: list[dict] | None = None,
    ) -> AIResponse:
        """Submit a tool execution result back to the AI.

        Used to continue the conversation after the AI called a tool.
        """
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for the given texts."""
        ...
