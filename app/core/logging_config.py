"""Logging configuration - compatibility wrapper."""

from app.core.logger import setup_structured_logging


def setup_logging() -> None:
    """Configure application logging (wrapper for structured logging)."""
    setup_structured_logging()
