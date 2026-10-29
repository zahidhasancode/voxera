"""FastAPI dependency injection (database session and IAM)."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exception_handlers import resolve_exception
from app.database.session import get_db_session
from app.infrastructure.iam.factory import build_iam_service


def _require_database() -> None:
    if not settings.database_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured. Set DATABASE_URL to enable the IAM APIs.",
        )


async def get_session(
    _: None = Depends(_require_database),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_iam_service(session: AsyncSession = Depends(get_session)):
    return build_iam_service(session)


def map_domain_errors(exc: Exception) -> HTTPException:
    """Map domain exceptions to HTTPException with standard error envelope."""
    status_code, body = resolve_exception(exc)
    return HTTPException(status_code=status_code, detail=body)
