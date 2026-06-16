"""MultiBot application entry point."""

import uvicorn

from src.api.app import create_app
from src.core.config import settings
from src.core.logging_config import setup_logging

setup_logging()

app = create_app(settings)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
