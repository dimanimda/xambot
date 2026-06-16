"""PluginRegistry — loads and manages integration plugins.

Week 1: stub implementation (returns empty tools, tool execution raises).
Week 2: loads manifest.yaml, registers tools, dispatches function calls.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.core.exceptions import ToolExecutionError
from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.plugins.base import Plugin

logger = get_logger(__name__)


class PluginRegistry:
    """Registry for integration plugins (Bitrix24, amoCRM, etc.).

    Each plugin is registered with its tools. The registry
    provides AI-compatible tool definitions and dispatches
    tool execution to the correct plugin.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, "Plugin"] = {}
        self._tool_map: dict[str, "Plugin"] = {}  # tool_name → plugin

    async def load_plugins(self, plugins_dir: str) -> None:
        """Scan directory for manifest.yaml files and load plugins.

        Week 2 implementation.
        """
        pass

    async def get_tools_for_ai(self, company_id: uuid.UUID | None = None) -> list[dict]:
        """Return all registered tools in AI-compatible format.

        Week 1: returns empty list.
        Week 2: returns tools from loaded plugin manifests.
        """
        return []

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        context: dict,
    ) -> dict:
        """Execute a registered tool.

        Week 1: always raises ToolExecutionError (no plugins loaded).
        Week 2: dispatches to the correct plugin.
        """
        logger.warning(
            "Tool execution requested but plugin system not yet active",
            tool_name=tool_name,
        )
        raise ToolExecutionError(
            f"Tool '{tool_name}' not found — plugin system is not yet active (Week 2)",
            code="TOOL_NOT_FOUND",
        )

    def register(self, plugin: "Plugin") -> None:
        """Register a plugin and its tools.

        Week 2: called during plugin loading.
        """
        self._plugins[plugin.name] = plugin
        # Tools would be registered here in Week 2
