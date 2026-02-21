"""Application configuration using Pydantic Settings.

This module provides environment-based configuration with presets for
development, staging, and production environments. All settings can be
overridden via environment variables.
"""

import json
import logging
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.environment import EnvironmentPresets

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables with environment-based defaults."""

    # Project
    PROJECT_NAME: str = Field(
        default="VOXERA Backend",
        description="Project name",
    )
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
        description="Environment: development, staging, or production",
    )

    # Server
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host address",
    )
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number",
    )
    RELOAD: Optional[bool] = Field(
        default=None,
        description="Auto-reload on code changes (None = auto-detect from ENVIRONMENT)",
    )
    WORKERS: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of worker processes (None = auto-detect from ENVIRONMENT)",
    )

    # CORS - Stored as string, accessed via cors_origins property
    CORS_ORIGINS: str = Field(
        default="",
        description="Allowed CORS origins (comma-separated string or JSON array string). Empty = use environment default",
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production-use-env-vars-min-32-chars",
        min_length=32,
        description="Secret key for encryption and JWT tokens",
    )

    # Twilio (optional: public base URL for TwiML stream URL in production)
    TWILIO_PUBLIC_BASE_URL: Optional[str] = Field(
        default=None,
        description="Public base URL for Twilio (e.g. https://your-domain.com). Used to build wss:// stream URL.",
    )

    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum concurrent WebSocket connections (None = auto-detect from ENVIRONMENT)",
    )
    WEBSOCKET_PING_INTERVAL: Optional[int] = Field(
        default=None,
        ge=1,
        description="WebSocket ping interval in seconds (None = auto-detect from ENVIRONMENT)",
    )
    WEBSOCKET_PING_TIMEOUT: Optional[int] = Field(
        default=None,
        ge=1,
        description="WebSocket ping timeout in seconds (None = auto-detect from ENVIRONMENT)",
    )

    # Logging
    LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="Log level (None = auto-detect from ENVIRONMENT). Options: DEBUG, INFO, WARNING, ERROR",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    def __init__(self, **kwargs):
        """Initialize settings and apply environment-based defaults."""
        super().__init__(**kwargs)
        self._apply_environment_defaults()

    def _apply_environment_defaults(self) -> None:
        """Apply environment-specific default values for settings that are None."""
        env = self.ENVIRONMENT.lower()

        # Apply CORS origins default if not set
        if not self.CORS_ORIGINS or not self.CORS_ORIGINS.strip():
            default_origins = EnvironmentPresets.get_cors_origins(env)
            self.CORS_ORIGINS = ",".join(default_origins)
            logger.debug(f"Applied default CORS origins for {env}: {default_origins}")

        # Apply server configuration defaults
        if self.RELOAD is None:
            server_config = EnvironmentPresets.get_server_config(env)
            self.RELOAD = server_config["reload"]
            logger.debug(f"Applied default RELOAD={self.RELOAD} for {env}")

        if self.WORKERS is None:
            server_config = EnvironmentPresets.get_server_config(env)
            self.WORKERS = server_config["workers"]
            logger.debug(f"Applied default WORKERS={self.WORKERS} for {env}")

        # Apply WebSocket configuration defaults
        if self.WEBSOCKET_MAX_CONNECTIONS is None:
            ws_config = EnvironmentPresets.get_websocket_config(env)
            self.WEBSOCKET_MAX_CONNECTIONS = ws_config["max_connections"]
            logger.debug(
                f"Applied default WEBSOCKET_MAX_CONNECTIONS={self.WEBSOCKET_MAX_CONNECTIONS} for {env}"
            )

        if self.WEBSOCKET_PING_INTERVAL is None:
            ws_config = EnvironmentPresets.get_websocket_config(env)
            self.WEBSOCKET_PING_INTERVAL = ws_config["ping_interval"]
            logger.debug(
                f"Applied default WEBSOCKET_PING_INTERVAL={self.WEBSOCKET_PING_INTERVAL} for {env}"
            )

        if self.WEBSOCKET_PING_TIMEOUT is None:
            ws_config = EnvironmentPresets.get_websocket_config(env)
            self.WEBSOCKET_PING_TIMEOUT = ws_config["ping_timeout"]
            logger.debug(
                f"Applied default WEBSOCKET_PING_TIMEOUT={self.WEBSOCKET_PING_TIMEOUT} for {env}"
            )

        # Apply log level default
        if self.LOG_LEVEL is None:
            self.LOG_LEVEL = EnvironmentPresets.get_log_level(env)
            logger.debug(f"Applied default LOG_LEVEL={self.LOG_LEVEL} for {env}")

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: Any) -> str:
        """Normalize environment value to lowercase."""
        if isinstance(v, str):
            return v.lower().strip()
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Safely convert CORS_ORIGINS string to List[str].
        
        Returns:
            List[str]: Parsed CORS origins, empty list if empty or invalid
            
        Supports:
        - Empty string: returns []
        - JSON array string: '["http://localhost:3000","http://localhost:8080"]'
        - Comma-separated string: "http://localhost:3000,http://localhost:8080"
        """
        if not self.CORS_ORIGINS or not self.CORS_ORIGINS.strip():
            return []

        value = self.CORS_ORIGINS.strip()

        # Try parsing as JSON array first
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    # Filter and validate items
                    result = [
                        str(item).strip()
                        for item in parsed
                        if item and str(item).strip()
                    ]
                    return result
            except (json.JSONDecodeError, TypeError, ValueError):
                # If JSON parsing fails, fall through to comma-separated parsing
                pass

        # Parse as comma-separated string
        try:
            parsed = [item.strip() for item in value.split(",") if item.strip()]
            return parsed
        except (AttributeError, TypeError):
            # If parsing fails, return empty list
            return []

    @property
    def DEBUG(self) -> bool:
        """Debug mode - True only in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"

    def get_log_level(self) -> str:
        """Get log level for current environment."""
        return self.LOG_LEVEL or EnvironmentPresets.get_log_level(self.ENVIRONMENT)

    def get_server_config(self) -> dict[str, Any]:
        """Get server configuration for current environment."""
        config = EnvironmentPresets.get_server_config(self.ENVIRONMENT)
        # Override with explicit settings if provided
        if self.RELOAD is not None:
            config["reload"] = self.RELOAD
        if self.WORKERS is not None:
            config["workers"] = self.WORKERS
        return config


settings = Settings()
