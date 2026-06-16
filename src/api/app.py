"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.ai.yais import YAISResponsesProvider
from src.api.middleware.error_handler import register_error_handlers
from src.api.middleware.request_id import RequestIDMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.webhooks import router as webhooks_router
from src.core.config import Settings
from src.plugins.registry import PluginRegistry


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MultiBot",
        version="0.1.0",
        description="Мультимессенджерная AI-платформа для бизнеса",
        docs_url="/docs" if settings.debug else None,
    )

    # ---- Middleware ----
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Error handlers ----
    register_error_handlers(app)

    # ---- Routes ----
    app.include_router(health_router, tags=["health"])
    app.include_router(webhooks_router)

    # ---- Application state (shared across requests) ----
    app.state.settings = settings

    # AI Provider (YAIS)
    app.state.ai_provider = YAISResponsesProvider(
        api_key=settings.yais_api_key,
        folder_id=settings.yais_folder_id,
        base_url=settings.yais_base_url,
        primary_model=settings.get_yais_model_url(),
        fallback_model=settings.yais_fallback_model,
    )

    # Plugin Registry (Week 1: empty — no integrations loaded)
    app.state.plugin_registry = PluginRegistry()

    return app
