"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.telephony.twilio_handler import router as twilio_router
from app.core.logger import get_logger
from app.core.logging_config import setup_logging
from app.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(
        "Starting VOXERA backend",
        extra_fields={
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0",
            "debug": settings.DEBUG,
        },
    )
    yield
    # Shutdown
    logger.info("Shutting down VOXERA backend")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    # Setup structured logging first
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

    # Request context middleware (must be first to set context)
    app.add_middleware(RequestContextMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers: API v1 (includes existing WebSocket at /api/v1/)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Twilio inbound voice (isolated: POST /twilio/inbound, WS /twilio/stream)
    app.include_router(twilio_router)

    return app


app = create_application()
