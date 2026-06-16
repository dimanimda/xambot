"""Text formatting utilities for MAX Messenger (Markdown / HTML)."""

from __future__ import annotations

import re
from typing import Any

from src.adapters.maxx.schemas import MaxButton

# Characters that have special meaning in MAX Markdown
_MARKDOWN_SPECIAL_CHARS = re.compile(r"([*_~`\[\]])")

# Characters that have special meaning in HTML
_HTML_SPECIAL_CHARS = {
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
}

# MAX default message length limit
_DEFAULT_MAX_LENGTH = 4096


class MaxMessageFormatter:
    """Format and sanitise text for MAX Messenger rendering.

    MAX supports:
    - **Markdown**: ``**bold**``, ``*italic*``, ``[text](url)``, ``code``, ``code blocks``
    - **HTML**: ``<b>``, ``<i>``, ``<a href>``, ``<code>``, ``<pre>``
    - **inline_keyboard**: rows of buttons

    Usage::

        fmt = MaxMessageFormatter()
        safe = fmt.format_markdown(user_input)        # escape user text
        keyboard = fmt.build_inline_keyboard(buttons)  # build reply markup
    """

    # ------------------------------------------------------------------
    # Markdown helpers
    # ------------------------------------------------------------------

    @staticmethod
    def format_markdown(text: str) -> str:
        """Escape Markdown special characters in arbitrary text.

        Escapes: ``*``, ``_``, ``~``, `````, ``[``, ``]``

        Use this on user-provided strings that should be displayed literally
        inside a Markdown-formatted message, not interpreted as markup.

        Args:
            text: Raw user text that may contain special chars.

        Returns:
            Escaped string safe for Markdown rendering.
        """
        return _MARKDOWN_SPECIAL_CHARS.sub(r"\\\1", text)

    @staticmethod
    def bold(text: str) -> str:
        """Wrap text in Markdown bold: ``**text**``."""
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """Wrap text in Markdown italic: ``*text*``."""
        return f"*{text}*"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a Markdown hyperlink: ``[text](url)``."""
        return f"[{text}]({url})"

    @staticmethod
    def code(text: str) -> str:
        """Wrap text in Markdown inline code: ``text``."""
        return f"`{text}`"

    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        """Wrap text in a Markdown fenced code block.

        Args:
            text: Code content.
            language: Optional language hint for syntax highlighting.
        """
        return f"```{language}\n{text}\n```"

    # ------------------------------------------------------------------
    # HTML helpers
    # ------------------------------------------------------------------

    @staticmethod
    def format_html(text: str) -> str:
        """Escape HTML special characters.

        Replaces ``&`` → ``&amp;``, ``<`` → ``&lt;``, ``>`` → ``&gt;``.
        Order matters: ``&`` is escaped first to avoid double-escaping.

        Args:
            text: Raw text that may contain HTML entities.

        Returns:
            Escaped string safe for HTML rendering.
        """
        result = text
        # Replace & first, then < and > — avoids re-escaping the ampersands
        # we just introduced
        for char in ("&", "<", ">"):
            result = result.replace(char, _HTML_SPECIAL_CHARS[char])
        return result

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def truncate_text(text: str, max_length: int = _DEFAULT_MAX_LENGTH) -> str:
        """Truncate text to a maximum length, appending ``…`` if cut.

        Args:
            text: Input text.
            max_length: Maximum allowed length in characters.

        Returns:
            Truncated text (same as input if within limit).
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 1] + "…"

    # ------------------------------------------------------------------
    # Inline keyboard builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_inline_keyboard(
        buttons: list[MaxButton],
        columns: int = 2,
    ) -> dict[str, Any]:
        """Build an inline_keyboard attachment structure for MAX API.

        Arranges buttons into rows of ``columns`` buttons each.

        Args:
            buttons: Flat list of :class:`MaxButton` instances.
            columns: Number of buttons per row (default 2).

        Returns:
            An attachment dict suitable for the ``attachments`` field in
            a MAX send-message request::

                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [
                            [{"type": "callback", "text": "A", "payload": "a"},
                             {"type": "callback", "text": "B", "payload": "b"}],
                            [{"type": "callback", "text": "C", "payload": "c"}],
                        ]
                    }
                }
        """
        rows: list[list[dict[str, Any]]] = []
        for i in range(0, len(buttons), columns):
            row_buttons = buttons[i : i + columns]
            rows.append([btn.model_dump(exclude_none=True) for btn in row_buttons])

        return {
            "type": "inline_keyboard",
            "payload": {
                "buttons": rows,
            },
        }
