"""Async database engine and session management."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Lazy initialization
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    url = database_url or settings.database_url
    return create_async_engine(
        url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
    )


def get_engine() -> AsyncEngine:
    """Return the singleton async engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def create_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory."""
    _engine = engine or create_engine()
    return async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    """FastAPI dependency: yield an async database session."""
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory()
    async with _session_factory() as session:
        yield session


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables (development only; use Alembic in production)."""
    from src.core.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection(engine: AsyncEngine) -> bool:
    """Health check: verify we can connect to the database."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        return False
