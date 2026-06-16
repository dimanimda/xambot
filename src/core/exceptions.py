"""Custom exception hierarchy for MultiBot."""


class MultiBotError(Exception):
    """Base exception for all MultiBot errors."""

    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "", code: str | None = None) -> None:
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


# ---- Tenant / Company ----

class TenantNotFoundError(MultiBotError):
    """Company not found by slug."""
    code = "TENANT_NOT_FOUND"


class TenantInactiveError(MultiBotError):
    """Company is deactivated."""
    code = "TENANT_INACTIVE"


# ---- AI Provider ----

class AIProviderError(MultiBotError):
    """Base for AI provider errors."""
    code = "AI_PROVIDER_ERROR"


class AITimeoutError(AIProviderError):
    """AI request timed out."""
    code = "AI_TIMEOUT"


class AIRateLimitError(AIProviderError):
    """AI rate limit exceeded."""
    code = "AI_RATE_LIMIT"


class AIAuthError(AIProviderError):
    """AI authentication failed."""
    code = "AI_AUTH_ERROR"


# ---- Messenger ----

class MessengerError(MultiBotError):
    """Base for messenger adapter errors."""
    code = "MESSENGER_ERROR"


class MessengerSendError(MessengerError):
    """Failed to send message via messenger."""
    code = "MESSENGER_SEND_ERROR"


class MaxAPIError(MessengerError):
    """MAX API returned an error (bad request, auth, rate limit, server)."""
    code = "MAX_API_ERROR"

    def __init__(
        self,
        message: str = "MAX API error",
        status_code: int | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message)


# ---- Plugins ----

class PluginError(MultiBotError):
    """Base for plugin errors."""
    code = "PLUGIN_ERROR"


class ToolExecutionError(PluginError):
    """Error during tool execution."""
    code = "TOOL_EXECUTION_ERROR"


class ToolNotFoundError(PluginError):
    """Requested tool not found in registry."""
    code = "TOOL_NOT_FOUND"


# ---- Data / Service ----

class CompanyNotFoundError(MultiBotError):
    """Company not found."""
    code = "COMPANY_NOT_FOUND"


class UserNotFoundError(MultiBotError):
    """User not found."""
    code = "USER_NOT_FOUND"


class ConversationNotFoundError(MultiBotError):
    """Conversation not found."""
    code = "CONVERSATION_NOT_FOUND"
