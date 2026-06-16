"""Abstract integration plugin interface."""

from abc import ABC, abstractmethod


class Plugin(ABC):
    """Abstract integration plugin.

    Each plugin (Bitrix24, amoCRM, etc.) implements this interface
    and provides a manifest.yaml with metadata and tool definitions.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        ...

    @abstractmethod
    async def initialize(self, config: dict) -> None:
        """Initialize the plugin with its configuration."""
        ...

    @abstractmethod
    async def execute_tool(
        self, tool_name: str, arguments: dict, context: dict
    ) -> dict:
        """Execute a tool call."""
        ...

    @abstractmethod
    async def get_tools(self) -> list[dict]:
        """Return tool definitions for AI provider."""
        ...
