"""Environment-based configuration presets."""

from typing import Dict, List


class EnvironmentPresets:
    """Environment-specific configuration presets."""

    # CORS origins per environment
    CORS_ORIGINS: Dict[str, List[str]] = {
        "development": [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ],
        "staging": [
            "https://staging.voxera.com",
            "https://staging-app.voxera.com",
        ],
        "production": [
            "https://voxera.com",
            "https://app.voxera.com",
        ],
    }

    # Log levels per environment
    LOG_LEVELS: Dict[str, str] = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING",
    }

    # Server configuration per environment
    SERVER_CONFIG: Dict[str, Dict[str, any]] = {
        "development": {
            "reload": True,
            "workers": 1,
        },
        "staging": {
            "reload": False,
            "workers": 2,
        },
        "production": {
            "reload": False,
            "workers": 4,
        },
    }

    # WebSocket configuration per environment
    WEBSOCKET_CONFIG: Dict[str, Dict[str, int]] = {
        "development": {
            "max_connections": 50,
            "ping_interval": 30,
            "ping_timeout": 10,
        },
        "staging": {
            "max_connections": 200,
            "ping_interval": 20,
            "ping_timeout": 10,
        },
        "production": {
            "max_connections": 1000,
            "ping_interval": 20,
            "ping_timeout": 10,
        },
    }

    @classmethod
    def get_cors_origins(cls, environment: str) -> List[str]:
        """Get CORS origins for environment."""
        return cls.CORS_ORIGINS.get(environment.lower(), cls.CORS_ORIGINS["development"])

    @classmethod
    def get_log_level(cls, environment: str) -> str:
        """Get log level for environment."""
        return cls.LOG_LEVELS.get(environment.lower(), "INFO")

    @classmethod
    def get_server_config(cls, environment: str) -> Dict[str, any]:
        """Get server configuration for environment."""
        return cls.SERVER_CONFIG.get(
            environment.lower(), cls.SERVER_CONFIG["development"]
        )

    @classmethod
    def get_websocket_config(cls, environment: str) -> Dict[str, int]:
        """Get WebSocket configuration for environment."""
        return cls.WEBSOCKET_CONFIG.get(
            environment.lower(), cls.WEBSOCKET_CONFIG["development"]
        )
