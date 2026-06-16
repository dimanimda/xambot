"""Global exception handler for FastAPI."""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""
    logger = structlog.get_logger(__name__)

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exception and return a 500 JSON response."""
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервера",
            },
        )
