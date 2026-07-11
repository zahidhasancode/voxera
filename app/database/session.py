"""Async database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine | None:
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    return _session_factory


async def init_database() -> None:
    """Create async engine and session factory (call from app lifespan)."""
    global _engine, _session_factory

    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL not set — enterprise persistence disabled")
        return

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    logger.info("Database engine initialized")


async def close_database() -> None:
    """Dispose engine on shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
    _engine = None
    _session_factory = None


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Unit-of-work scope for services (commit/rollback)."""
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("Database is not configured (DATABASE_URL missing)")

    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_database_connectivity() -> bool:
    """Return True when database accepts a simple query."""
    from sqlalchemy import text

    factory = get_session_factory()
    if factory is None:
        return False
    try:
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields session; commits on success, rolls back on error."""
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("Database is not configured (DATABASE_URL missing)")

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
