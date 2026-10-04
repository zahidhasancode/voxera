"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.core.timeout import RequestTimeoutMiddleware
from app.database import close_database, init_database
from app.iam.middleware.authentication import AuthenticationMiddleware
from app.telephony.twilio_handler import router as twilio_router
from app.core.logger import get_logger
from app.core.logging_config import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.shutdown import shutdown_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(
        "Starting VOXERA backend",
        extra_fields={
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0",
            "debug": settings.DEBUG,
            "database_enabled": settings.database_enabled,
        },
    )
    await init_database()
    settings.validate_security_settings()
    from app.voice.registry import validate_voice_platform

    if settings.database_enabled:
        from app.infrastructure.knowledge.providers import validate_knowledge_platform

        await validate_knowledge_platform()
    await validate_voice_platform()
    yield
    logger.info("Initiating graceful shutdown")
    await shutdown_manager.initiate_shutdown(
        drain_timeout_seconds=settings.SHUTDOWN_DRAIN_TIMEOUT_SECONDS
    )
    await shutdown_manager.close_websockets()
    from app.voice.http import close_http_client

    await close_http_client()
    await close_database()
    logger.info("VOXERA backend shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    setup_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Production-ready FastAPI backend for VOXERA",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    # Middleware: last added = outermost (first on inbound request)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RequestTimeoutMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(twilio_router)

    return app


app = create_application()
