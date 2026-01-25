"""Central logger module with structured JSON logging and context propagation."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings

# Context variables for async-safe request/call ID propagation
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
call_id_var: ContextVar[Optional[str]] = ContextVar("call_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    SERVICE_NAME = "voxera-backend"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": self.SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add call_id if available
        call_id = call_id_var.get()
        if call_id:
            log_data["call_id"] = call_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from log record
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_data.update(record.extra_fields)

        # Add module, function, line number for debug logs
        if record.levelno <= logging.DEBUG:
            log_data["module"] = record.module
            log_data["function"] = record.funcName
            log_data["line"] = record.lineno

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Structured logger wrapper with context support."""

    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)

    def _log_with_context(
        self,
        level: int,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log with context and extra fields."""
        extra = kwargs.get("extra", {})
        if extra_fields:
            extra["extra_fields"] = extra_fields
        kwargs["extra"] = extra
        self.logger.log(level, message, *args, **kwargs)

    def debug(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, *args, extra_fields=extra_fields, **kwargs)

    def info(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, *args, extra_fields=extra_fields, **kwargs)

    def warning(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log warning message."""
        self._log_with_context(
            logging.WARNING, message, *args, extra_fields=extra_fields, **kwargs
        )

    def error(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, *args, extra_fields=extra_fields, **kwargs)

    def exception(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log exception with traceback."""
        kwargs["exc_info"] = True
        self._log_with_context(
            logging.ERROR, message, *args, extra_fields=extra_fields, **kwargs
        )

    def critical(
        self,
        message: str,
        *args: Any,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log critical message."""
        self._log_with_context(
            logging.CRITICAL, message, *args, extra_fields=extra_fields, **kwargs
        )


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def setup_structured_logging() -> None:
    """Configure structured JSON logging."""
    # Get log level from settings
    log_level_name = settings.get_log_level()
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Console handler - JSON output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(json_formatter)

    # File handler - JSON output
    file_handler = logging.FileHandler(log_dir / "voxera.json")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").propagate = False

    # Prevent duplicate logs
    logging.getLogger("uvicorn").propagate = False


def set_request_id(request_id: Optional[str]) -> None:
    """Set request ID in context."""
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def set_call_id(call_id: Optional[str]) -> None:
    """Set call ID in context."""
    call_id_var.set(call_id)


def get_call_id() -> Optional[str]:
    """Get current call ID from context."""
    return call_id_var.get()


def clear_context() -> None:
    """Clear all context variables."""
    request_id_var.set(None)
    call_id_var.set(None)
