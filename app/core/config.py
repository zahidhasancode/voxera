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

_INSECURE_DEFAULT_SECRET = "change-this-secret-key-in-production-use-env-vars-min-32-chars"


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

    # Security — separate keys (required in staging/production when DATABASE_URL is set)
    JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        min_length=32,
        description="HS256 signing key for JWT access and refresh tokens",
    )
    API_KEY_SECRET: Optional[str] = Field(
        default=None,
        min_length=32,
        description="HMAC key for API key hashing and verification",
    )
    ENCRYPTION_SECRET_KEY: Optional[str] = Field(
        default=None,
        min_length=32,
        description="Key for field-level encryption via LocalSecretProvider",
    )
    SECRET_KEY: Optional[str] = Field(
        default=None,
        min_length=32,
        description="Legacy single secret; dev-only fallback when separate keys are unset",
    )

    # Twilio webhook signature validation
    TWILIO_AUTH_TOKEN: Optional[str] = Field(
        default=None,
        description="Twilio auth token for X-Twilio-Signature validation on inbound webhooks",
    )

    # Twilio (optional: public base URL for TwiML stream URL in production)
    TWILIO_PUBLIC_BASE_URL: Optional[str] = Field(
        default=None,
        description="Public base URL for Twilio (e.g. https://your-domain.com). Used to build wss:// stream URL.",
    )
    TWILIO_STREAM_TOKEN_TTL_SECONDS: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Max age of signed Media Stream tokens (replay protection)",
    )

    # Voice providers (STT / LLM / TTS)
    VOICE_REQUIRE_PROVIDERS: bool = Field(
        default=False,
        description="Fail startup when voice providers are not configured and healthy",
    )
    STT_PROVIDER: str | None = Field(default=None, description="STT provider identifier")
    LLM_PROVIDER: str | None = Field(default=None, description="Streaming LLM provider identifier")
    TTS_PROVIDER: str | None = Field(default=None, description="Streaming TTS provider identifier")
    VOICE_LLM_MODEL: str = Field(default="gpt-4o-mini", description="Default LLM model for voice")
    VOICE_LLM_SYSTEM_PROMPT: str = Field(
        default="You are a helpful voice assistant. Respond concisely in spoken language.",
    )
    VOICE_LLM_MAX_TOKENS: int = Field(default=512, ge=32, le=4096)
    VOICE_LLM_TIMEOUT_SECONDS: float = Field(default=8.0, ge=1.0, le=120.0)
    VOICE_LLM_FAILOVER_PROVIDER: str | None = Field(
        default=None,
        description="Secondary LLM provider for failover",
    )
    VOICE_TTS_VOICE_ID: str | None = Field(default=None, description="Provider-specific voice identifier")
    VOICE_TTS_MODEL: str = Field(default="tts-1", description="OpenAI TTS model when using openai_audio")
    VOICE_SAMPLE_RATE: int = Field(default=16000, ge=8000, le=48000)
    VOICE_FRAME_MS: int = Field(default=20, ge=10, le=60)
    VOICE_PCM_FRAME_BYTES: int = Field(default=640, ge=320, le=4096)
    VOICE_ALLOW_MOCK_PROVIDERS: Optional[bool] = Field(
        default=None,
        description=(
            "Use built-in mock STT/LLM/TTS engines when a provider is not configured. "
            "None = allowed in development only. Never allowed in production."
        ),
    )
    VOICE_HISTORY_TURNS: int = Field(
        default=8, ge=0, le=50, description="Earlier user/assistant turns sent to the LLM as context"
    )
    VOICE_TTS_MAX_LEAD_MS: int = Field(
        default=250, ge=0, le=5000,
        description="How far ahead of real-time playback speech audio may be sent (bounds what a barge-in must discard)",
    )
    DEEPGRAM_ENDPOINTING_MS: int = Field(
        default=300, ge=10, le=5000, description="Silence after speech before Deepgram marks the turn finished"
    )
    DEEPGRAM_UTTERANCE_END_MS: int = Field(
        default=1000, ge=1000, le=5000,
        description="Fallback end-of-utterance signal when endpointing does not fire (noisy audio)",
    )
    DEEPGRAM_API_KEY: Optional[str] = Field(default=None)
    DEEPGRAM_MODEL: str = Field(default="nova-2")
    DEEPGRAM_LANGUAGE: str = Field(default="en")
    ASSEMBLYAI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_SPEECH_CREDENTIALS_JSON: Optional[str] = Field(default=None)
    AZURE_SPEECH_KEY: Optional[str] = Field(default=None)
    AZURE_SPEECH_REGION: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-haiku-latest")
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None)
    ELEVENLABS_MODEL: str = Field(default="eleven_turbo_v2_5")
    AZURE_TTS_KEY: Optional[str] = Field(default=None)
    AZURE_TTS_REGION: Optional[str] = Field(default=None)
    AZURE_TTS_VOICE: str = Field(default="en-US-JennyNeural")
    CARTESIA_API_KEY: Optional[str] = Field(default=None)
    CARTESIA_VOICE_ID: Optional[str] = Field(default=None)
    VOICE_OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI key for voice LLM/TTS; falls back to OPENAI_API_KEY",
    )
    VOICE_IDLE_TIMEOUT_SECONDS: float = Field(default=300.0, ge=30.0, le=3600.0)
    VOICE_MAX_CONCURRENT_CALLS: int = Field(default=1000, ge=1, le=10000)

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

    # Database (enterprise multi-tenant persistence)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@localhost:5432/voxera",
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL statements (development only)",
    )
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100)

    # Knowledge ingestion
    KNOWLEDGE_STORAGE_PATH: str = Field(
        default="data/knowledge",
        description="Local filesystem path for uploaded knowledge files",
    )
    KNOWLEDGE_DEFAULT_CHUNK_SIZE: int = Field(default=512, ge=64, le=8192)
    KNOWLEDGE_DEFAULT_CHUNK_OVERLAP: int = Field(default=64, ge=0, le=2048)
    KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER: str | None = Field(
        default=None,
        description="Embedding provider identifier (openai, voyageai, bge, etc.)",
    )
    KNOWLEDGE_DEFAULT_VECTOR_STORE: str | None = Field(
        default=None,
        description="Vector store identifier (qdrant, pinecone, pgvector, etc.)",
    )
    KNOWLEDGE_MAX_UPLOAD_BYTES: int = Field(
        default=52_428_800,
        ge=1,
        description="Maximum upload size in bytes (default 50 MB)",
    )
    KNOWLEDGE_REQUIRE_PROVIDERS: bool = Field(
        default=False,
        description="Fail startup if embedding/vector providers are not configured and healthy",
    )
    KNOWLEDGE_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Default embedding model name for OpenAI-compatible providers",
    )
    KNOWLEDGE_EMBEDDING_DIMENSIONS: int = Field(default=1536, ge=128, le=4096)
    KNOWLEDGE_EMBEDDING_BATCH_SIZE: int = Field(default=64, ge=1, le=512)
    KNOWLEDGE_JOB_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    KNOWLEDGE_JOB_RETRY_DELAY_SECONDS: int = Field(default=30, ge=1, le=600)
    KNOWLEDGE_CACHE_TTL_SECONDS: int = Field(default=3600, ge=0, le=86400)
    KNOWLEDGE_ALLOWED_EXTENSIONS: str = Field(
        default="pdf,docx,txt,md,csv,html,htm",
        description="Comma-separated allowed upload extensions",
    )
    # Provider credentials
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1")
    VOYAGE_API_KEY: Optional[str] = Field(default=None)
    VOYAGE_API_BASE: str = Field(default="https://api.voyageai.com/v1")
    NOMIC_API_KEY: Optional[str] = Field(default=None)
    NOMIC_API_BASE: str = Field(default="https://api-atlas.nomic.ai/v1")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_CHAT_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-01")
    BGE_EMBEDDING_URL: Optional[str] = Field(
        default=None,
        description="OpenAI-compatible embedding endpoint for self-hosted BGE",
    )
    BGE_API_KEY: Optional[str] = Field(default=None)
    QDRANT_URL: Optional[str] = Field(default=None)
    QDRANT_API_KEY: Optional[str] = Field(default=None)
    PINECONE_API_KEY: Optional[str] = Field(default=None)
    PINECONE_INDEX_HOST: Optional[str] = Field(default=None)
    WEAVIATE_URL: Optional[str] = Field(default=None)
    WEAVIATE_API_KEY: Optional[str] = Field(default=None)
    MILVUS_URI: Optional[str] = Field(default=None)
    MILVUS_TOKEN: Optional[str] = Field(default=None)
    MILVUS_COLLECTION: str = Field(default="voxera_knowledge")

    # Enterprise RAG / retrieval engine
    RAG_CACHE_TTL_SECONDS: int = Field(default=300, ge=0, le=86400)
    RAG_EMBEDDING_CACHE_TTL_SECONDS: int = Field(default=3600, ge=0, le=86400)
    RAG_MAX_CONTEXT_TOKENS: int = Field(default=4096, ge=256, le=128000)
    RAG_MIN_SIMILARITY_THRESHOLD: float = Field(default=0.65, ge=0.0, le=1.0)
    RAG_DEFAULT_TOP_K: int = Field(default=8, ge=1, le=100)
    RAG_VECTOR_SEARCH_TARGET_MS: int = Field(default=100, ge=1)
    RAG_CONTEXT_BUILD_TARGET_MS: int = Field(default=30, ge=1)
    RAG_PROMPT_BUILD_TARGET_MS: int = Field(default=20, ge=1)
    RAG_ENABLE_RETRIEVAL_CACHE: bool = Field(default=True)

    # Enterprise memory system
    MEMORY_MAX_CONTEXT_TOKENS: int = Field(default=8192, ge=256, le=128000)
    MEMORY_SUMMARY_TURN_THRESHOLD: int = Field(default=12, ge=4, le=200)
    MEMORY_COMPRESSION_ENABLED: bool = Field(default=True)
    MEMORY_CACHE_TTL_SECONDS: int = Field(default=300, ge=0, le=86400)
    MEMORY_WORKING_MEMORY_TTL_SECONDS: int = Field(default=3600, ge=60, le=86400)
    MEMORY_SESSION_EXPIRY_HOURS: int = Field(default=24, ge=1, le=168)
    MEMORY_MAX_TURNS_BEFORE_COMPRESS: int = Field(default=20, ge=5, le=500)

    # Enterprise tool execution framework
    TOOL_EXECUTION_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=300.0)
    TOOL_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    TOOL_RETRY_BASE_DELAY_MS: int = Field(default=200, ge=50, le=10000)
    TOOL_CIRCUIT_FAILURE_THRESHOLD: int = Field(default=5, ge=1, le=100)
    TOOL_CIRCUIT_RECOVERY_SECONDS: int = Field(default=60, ge=5, le=3600)
    TOOL_RATE_LIMIT_PER_MINUTE: int = Field(default=120, ge=1, le=10000)
    TOOL_ALLOWED_HTTP_HOSTS: str = Field(
        default="",
        description="Comma-separated allowlist of HTTP webhook hosts (empty = block all HTTP tools)",
    )
    TOOL_ENABLE_BUILTIN_TOOLS: bool = Field(default=True)

    # Enterprise planner agent
    PLANNER_MAX_REASONING_STEPS: int = Field(default=5, ge=1, le=20)
    PLANNER_MIN_CONFIDENCE: float = Field(default=0.55, ge=0.0, le=1.0)
    PLANNER_CACHE_TTL_SECONDS: int = Field(default=300, ge=0, le=86400)
    PLANNER_MAX_CONTEXT_TOKENS: int = Field(default=6144, ge=256, le=128000)
    PLANNER_ENABLE_CACHE: bool = Field(default=True)
    PLANNER_DEFAULT_LANGUAGE: str = Field(default="en", max_length=16)
    PLANNER_MODEL_PROVIDER: str = Field(
        default="structured",
        description="Planner model provider: structured, openai, anthropic, gemini, azure, groq, local",
    )
    PLANNER_ESCALATION_CONFIDENCE_THRESHOLD: float = Field(default=0.40, ge=0.0, le=1.0)

    # Enterprise verifier agent
    VERIFIER_CACHE_TTL_SECONDS: int = Field(default=300, ge=0, le=86400)
    VERIFIER_ENABLE_CACHE: bool = Field(default=True)
    VERIFIER_MIN_CONFIDENCE: float = Field(default=0.50, ge=0.0, le=1.0)
    VERIFIER_KNOWLEDGE_MIN_SIMILARITY: float = Field(default=0.65, ge=0.0, le=1.0)
    VERIFIER_MODEL_PROVIDER: str = Field(
        default="structured",
        description="Verifier model provider: structured, openai, anthropic, gemini, groq, local",
    )
    VERIFIER_REFUND_HUMAN_THRESHOLD_USD: float = Field(default=500.0, ge=0.0)
    VERIFIER_AUTO_APPROVE_LOW_RISK: bool = Field(default=True)

    # Enterprise workflow & policy engine
    WORKFLOW_DEFAULT_TIMEOUT_SECONDS: int = Field(default=3600, ge=60, le=86400)
    WORKFLOW_APPROVAL_TIMEOUT_SECONDS: int = Field(default=1800, ge=60, le=86400)
    WORKFLOW_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    WORKFLOW_RETRY_DELAY_SECONDS: int = Field(default=30, ge=1, le=3600)
    WORKFLOW_DEFAULT_TIMEZONE: str = Field(default="UTC", max_length=64)
    WORKFLOW_ENABLE_EVENT_BUS: bool = Field(default=True)
    WORKFLOW_MAX_STEPS: int = Field(default=50, ge=1, le=500)

    # Enterprise IAM
    IAM_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440)
    IAM_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, ge=1, le=365)
    IAM_SESSION_MAX_CONCURRENT: int = Field(default=10, ge=1, le=100)
    IAM_API_KEY_PREFIX: str = Field(default="vx_", max_length=16)
    IAM_PASSWORD_MIN_LENGTH: int = Field(default=12, ge=8, le=128)
    IAM_MFA_ISSUER: str = Field(default="VOXERA", max_length=64)
    IAM_MAGIC_LINK_EXPIRE_MINUTES: int = Field(default=15, ge=5, le=60)
    IAM_ENABLE_API_KEY_AUTH: bool = Field(default=True)
    IAM_SECRET_PROVIDER: str = Field(
        default="local",
        description="Secret provider: local, aws_secrets_manager, azure_key_vault, gcp_secret_manager, vault",
    )

    # Platform reliability
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1, le=3600)
    RATE_LIMIT_PER_IP: int = Field(default=300, ge=1, le=100000)
    RATE_LIMIT_PER_ENDPOINT: int = Field(default=120, ge=1, le=100000)
    RATE_LIMIT_PER_ORGANIZATION: int = Field(default=600, ge=1, le=1000000)
    REQUEST_TIMEOUT_ENABLED: bool = Field(default=True)
    REQUEST_TIMEOUT_DEFAULT_SECONDS: float = Field(default=30.0, ge=1.0, le=600.0)
    REQUEST_TIMEOUT_KNOWLEDGE_SECONDS: float = Field(default=45.0, ge=1.0, le=600.0)
    REQUEST_TIMEOUT_PLANNER_SECONDS: float = Field(default=60.0, ge=1.0, le=600.0)
    REQUEST_TIMEOUT_VERIFIER_SECONDS: float = Field(default=60.0, ge=1.0, le=600.0)
    REQUEST_TIMEOUT_TOOLS_SECONDS: float = Field(default=45.0, ge=1.0, le=600.0)
    REQUEST_TIMEOUT_WORKFLOW_SECONDS: float = Field(default=90.0, ge=1.0, le=600.0)
    SHUTDOWN_DRAIN_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=300.0)

    @property
    def voice_openai_api_key(self) -> str | None:
        return self.VOICE_OPENAI_API_KEY or self.OPENAI_API_KEY

    @property
    def knowledge_allowed_extensions(self) -> frozenset[str]:
        return frozenset(
            ext.strip().lower().lstrip(".")
            for ext in self.KNOWLEDGE_ALLOWED_EXTENSIONS.split(",")
            if ext.strip()
        )

    @property
    def tool_allowed_http_hosts(self) -> list[str]:
        if not self.TOOL_ALLOWED_HTTP_HOSTS.strip():
            return []
        return [h.strip().lower() for h in self.TOOL_ALLOWED_HTTP_HOSTS.split(",") if h.strip()]

    @property
    def database_enabled(self) -> bool:
        """True when DATABASE_URL is configured."""
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip())

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
    def voice_mocks_allowed(self) -> bool:
        """Whether mock voice engines may stand in for unconfigured providers."""
        if self.is_production:
            return False
        if self.VOICE_ALLOW_MOCK_PROVIDERS is not None:
            return self.VOICE_ALLOW_MOCK_PROVIDERS
        return self.is_development

    @property
    def voice_dev_messages_enabled(self) -> bool:
        """Whether the dev_test_* WebSocket messages are accepted (development only)."""
        return self.is_development

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

    def _resolve_secret(self, specific: Optional[str], purpose: str) -> str:
        """Resolve a secret key with dev-only legacy fallback."""
        if specific and specific.strip():
            value = specific.strip()
            if value == _INSECURE_DEFAULT_SECRET and (self.is_production or self.is_staging):
                raise RuntimeError(f"{purpose} must not use the insecure default value in {self.ENVIRONMENT}")
            return value
        legacy = (self.SECRET_KEY or "").strip()
        if legacy:
            if legacy == _INSECURE_DEFAULT_SECRET and (self.is_production or self.is_staging):
                raise RuntimeError(
                    f"{purpose} is not configured and legacy SECRET_KEY uses the insecure default "
                    f"in {self.ENVIRONMENT}. Set JWT_SECRET_KEY, API_KEY_SECRET, and ENCRYPTION_SECRET_KEY."
                )
            if self.is_development:
                logger.warning(
                    "%s not set; using legacy SECRET_KEY (development only)",
                    purpose,
                )
                return legacy
        raise RuntimeError(
            f"{purpose} is required. Set the dedicated environment variable "
            f"(or SECRET_KEY in development only)."
        )

    @property
    def jwt_secret_key(self) -> str:
        return self._resolve_secret(self.JWT_SECRET_KEY, "JWT_SECRET_KEY")

    @property
    def api_key_secret(self) -> str:
        return self._resolve_secret(self.API_KEY_SECRET, "API_KEY_SECRET")

    @property
    def encryption_secret_key(self) -> str:
        return self._resolve_secret(self.ENCRYPTION_SECRET_KEY, "ENCRYPTION_SECRET_KEY")

    def validate_security_settings(self) -> None:
        """Fail fast when security secrets are missing or insecure."""
        if not self.database_enabled:
            return
        if not (self.is_production or self.is_staging):
            # Development: resolve keys (may fall back to SECRET_KEY) to surface misconfiguration early
            _ = self.jwt_secret_key
            _ = self.api_key_secret
            _ = self.encryption_secret_key
            return
        for name, value in (
            ("JWT_SECRET_KEY", self.jwt_secret_key),
            ("API_KEY_SECRET", self.api_key_secret),
            ("ENCRYPTION_SECRET_KEY", self.encryption_secret_key),
        ):
            if not value or len(value) < 32:
                raise RuntimeError(f"{name} must be at least 32 characters in {self.ENVIRONMENT}")
        if self.TWILIO_AUTH_TOKEN is None and self.TWILIO_PUBLIC_BASE_URL:
            logger.warning(
                "TWILIO_AUTH_TOKEN is not set but TWILIO_PUBLIC_BASE_URL is configured; "
                "Twilio webhook signature validation will reject inbound calls"
            )


settings = Settings()
