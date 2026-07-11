"""Standard API error response models and builders."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logger import get_request_id


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    REQUEST_TIMEOUT = "request_timeout"
    DATABASE_ERROR = "database_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TOOL_ERROR = "tool_error"
    WORKFLOW_ERROR = "workflow_error"
    PLANNER_ERROR = "planner_error"
    VERIFIER_ERROR = "verifier_error"
    MEMORY_ERROR = "memory_error"
    RETRIEVAL_ERROR = "retrieval_error"
    INTERNAL_ERROR = "internal_error"


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None
    request_id: str | None = None
    timestamp: str
    documentation_url: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


def error_documentation_url(code: str) -> str:
    return f"https://docs.voxera.ai/errors/{code}"


def build_error_response(
    *,
    code: str | ErrorCode,
    message: str,
    details: Any | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    code_str = code.value if isinstance(code, ErrorCode) else code
    rid = request_id or get_request_id()
    return {
        "success": False,
        "error": {
            "code": code_str,
            "message": message,
            "details": details,
            "request_id": rid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "documentation_url": error_documentation_url(code_str),
        },
    }
