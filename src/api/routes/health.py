"""Health check endpoints — liveness and readiness probes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.database import check_db_connection, get_engine

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Liveness probe. Returns 200 if the application is running."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe. Checks database connectivity."""
    engine = get_engine()
    db_ok = await check_db_connection(engine)
    status_code = 200 if db_ok else 503
    return JSONResponse(
        content={
            "status": "ready" if db_ok else "not_ready",
            "database": db_ok,
        },
        status_code=status_code,
    )
