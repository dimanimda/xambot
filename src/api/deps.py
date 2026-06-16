"""FastAPI dependency injection."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.base import AIProvider
from src.core.database import get_session


async def get_db() -> AsyncSession:
    """Dependency: yield an async database session.

    Automatically closed after the request completes.
    """
    async for session in get_session():
        yield session


def get_settings():
    """Dependency: return application settings (lazy import to avoid circular deps)."""
    from src.core.config import settings
    return settings


async def get_ai_provider(request: Request) -> AIProvider:
    """Dependency: return the shared AI provider instance.

    The provider is initialised once at application startup
    and stored on ``app.state.ai_provider``.
    """
    return request.app.state.ai_provider


def get_plugin_registry(request: Request):
    """Dependency: return the shared plugin registry.

    Week 1: returns an empty ``PluginRegistry`` (no integrations loaded).
    Week 2: returns a registry with loaded plugin manifests.
    """
    return getattr(request.app.state, "plugin_registry", None)
