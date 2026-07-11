"""Centralized exception-to-HTTP response mapping."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError

from app.core.errors import ErrorCode, build_error_response
from app.core.exceptions import (
    ApiKeyNotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    CrossOrganizationAccessError,
    CrossTenantMemoryError,
    CrossTenantPlannerError,
    CrossTenantToolError,
    CrossTenantVerifierError,
    CrossTenantWorkflowError,
    DatabaseUnavailableError,
    IamSessionNotFoundError,
    IamUserNotFoundError,
    IamValidationError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    MemoryAccessError,
    MfaRequiredError,
    NotFoundError,
    OrganizationNotFoundError,
    PlannerConfidenceTooLowError,
    PlannerPolicyViolationError,
    PlannerSessionNotFoundError,
    PlannerValidationError,
    RetrievalValidationError,
    SecurityPolicyViolationError,
    SessionExpiredError,
    SessionNotFoundError,
    TokenExpiredError,
    ToolCircuitOpenError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolRateLimitError,
    ToolValidationError,
    VerifierComplianceError,
    VerifierPolicyViolationError,
    VerifierRejectionError,
    VerifierValidationError,
    WorkflowApprovalRequiredError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
    WorkflowPolicyViolationError,
    WorkflowValidationError,
)
from app.core.logger import get_logger, get_request_id
from app.core.observability import platform_metrics

logger = get_logger(__name__)


def resolve_exception(exc: Exception) -> tuple[int, dict[str, Any]]:
    """Map any exception to (status_code, standard error body)."""
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and detail.get("success") is False and "error" in detail:
            return exc.status_code, detail
        if isinstance(detail, dict):
            message = detail.get("message", str(detail))
            details = detail
        else:
            message = str(detail)
            details = None
        code = _code_from_status(exc.status_code)
        return exc.status_code, build_error_response(code=code, message=message, details=details)

    if isinstance(exc, RequestValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            details=exc.errors(),
        )

    if isinstance(exc, asyncio.TimeoutError):
        return status.HTTP_504_GATEWAY_TIMEOUT, build_error_response(
            code=ErrorCode.REQUEST_TIMEOUT,
            message="Request timed out",
        )

    if isinstance(exc, IntegrityError):
        return status.HTTP_409_CONFLICT, build_error_response(
            code=ErrorCode.CONFLICT,
            message="Database constraint violation",
            details={"type": "integrity_error"},
        )

    if isinstance(exc, (OperationalError, DBAPIError)):
        platform_metrics.record_dependency_failure("database")
        return status.HTTP_503_SERVICE_UNAVAILABLE, build_error_response(
            code=ErrorCode.DATABASE_ERROR,
            message="Database operation failed",
        )

    if isinstance(exc, SQLAlchemyError):
        platform_metrics.record_dependency_failure("database")
        return status.HTTP_503_SERVICE_UNAVAILABLE, build_error_response(
            code=ErrorCode.DATABASE_ERROR,
            message="Database error",
        )

    if isinstance(exc, NotFoundError):
        code = ErrorCode.NOT_FOUND
        if isinstance(exc, (ToolNotFoundError, WorkflowNotFoundError, SessionNotFoundError, PlannerSessionNotFoundError)):
            code = _domain_code(exc)
        return status.HTTP_404_NOT_FOUND, build_error_response(code=code, message=str(exc))

    if isinstance(exc, ConflictError):
        return status.HTTP_409_CONFLICT, build_error_response(code=ErrorCode.CONFLICT, message=str(exc))

    if isinstance(exc, DatabaseUnavailableError):
        platform_metrics.record_dependency_failure("database")
        return status.HTTP_503_SERVICE_UNAVAILABLE, build_error_response(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=str(exc),
        )

    if isinstance(exc, RetrievalValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.RETRIEVAL_ERROR,
            message=str(exc),
            details={"violations": exc.violations},
        )

    if isinstance(exc, (MemoryAccessError, CrossTenantMemoryError, SessionExpiredError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.MEMORY_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, (ToolPermissionDeniedError, CrossTenantToolError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.TOOL_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, ToolValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.TOOL_ERROR,
            message=str(exc),
            details={"violations": exc.violations},
        )

    if isinstance(exc, ToolRateLimitError):
        return status.HTTP_429_TOO_MANY_REQUESTS, build_error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=str(exc),
        )

    if isinstance(exc, (ToolExecutionError, ToolCircuitOpenError)):
        code_status = status.HTTP_503_SERVICE_UNAVAILABLE if getattr(exc, "retryable", False) else status.HTTP_500_INTERNAL_SERVER_ERROR
        return code_status, build_error_response(code=ErrorCode.TOOL_ERROR, message=str(exc))

    if isinstance(exc, (PlannerPolicyViolationError, CrossTenantPlannerError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.PLANNER_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, PlannerValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.PLANNER_ERROR,
            message=str(exc),
            details={"violations": exc.violations},
        )

    if isinstance(exc, PlannerConfidenceTooLowError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.PLANNER_ERROR,
            message=str(exc),
            details={"confidence": exc.confidence},
        )

    if isinstance(exc, (VerifierPolicyViolationError, CrossTenantVerifierError, VerifierRejectionError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.VERIFIER_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, (VerifierValidationError, VerifierComplianceError)):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.VERIFIER_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, (CrossTenantWorkflowError, WorkflowPolicyViolationError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.WORKFLOW_ERROR,
            message=str(exc),
            details={"violations": getattr(exc, "violations", [])},
        )

    if isinstance(exc, WorkflowApprovalRequiredError):
        return status.HTTP_409_CONFLICT, build_error_response(
            code=ErrorCode.WORKFLOW_ERROR,
            message=str(exc),
            details={"approval_id": exc.approval_id},
        )

    if isinstance(exc, WorkflowValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.WORKFLOW_ERROR,
            message=str(exc),
            details={"violations": exc.violations},
        )

    if isinstance(exc, WorkflowExecutionError):
        code_status = status.HTTP_503_SERVICE_UNAVAILABLE if exc.retryable else status.HTTP_500_INTERNAL_SERVER_ERROR
        return code_status, build_error_response(code=ErrorCode.WORKFLOW_ERROR, message=str(exc))

    if isinstance(exc, (InvalidCredentialsError, AuthenticationError, TokenExpiredError)):
        return status.HTTP_401_UNAUTHORIZED, build_error_response(
            code=ErrorCode.AUTHENTICATION_ERROR,
            message=str(exc),
        )

    if isinstance(exc, MfaRequiredError):
        return status.HTTP_401_UNAUTHORIZED, build_error_response(
            code=ErrorCode.AUTHENTICATION_ERROR,
            message=str(exc),
            details={"challenge_id": exc.challenge_id},
        )

    if isinstance(exc, (InsufficientPermissionsError, AuthorizationError, CrossOrganizationAccessError)):
        return status.HTTP_403_FORBIDDEN, build_error_response(
            code=ErrorCode.AUTHORIZATION_ERROR,
            message=str(exc),
            details={"permission": getattr(exc, "permission", None)},
        )

    if isinstance(exc, (OrganizationNotFoundError, IamUserNotFoundError, ApiKeyNotFoundError, IamSessionNotFoundError)):
        return status.HTTP_404_NOT_FOUND, build_error_response(code=ErrorCode.NOT_FOUND, message=str(exc))

    if isinstance(exc, (IamValidationError, SecurityPolicyViolationError)):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, build_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(exc),
            details={"violations": exc.violations},
        )

    if isinstance(exc, ValueError):
        return status.HTTP_400_BAD_REQUEST, build_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(exc),
        )

    if isinstance(exc, RuntimeError) and "shutting down" in str(exc).lower():
        return status.HTTP_503_SERVICE_UNAVAILABLE, build_error_response(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Server is shutting down",
        )

    return status.HTTP_500_INTERNAL_SERVER_ERROR, build_error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
    )


def _code_from_status(status_code: int) -> ErrorCode:
    mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.REQUEST_TIMEOUT,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)


def _domain_code(exc: Exception) -> ErrorCode:
    name = type(exc).__name__
    if "Tool" in name:
        return ErrorCode.TOOL_ERROR
    if "Workflow" in name:
        return ErrorCode.WORKFLOW_ERROR
    if "Planner" in name:
        return ErrorCode.PLANNER_ERROR
    if "Verifier" in name:
        return ErrorCode.VERIFIER_ERROR
    if "Memory" in name or "Session" in name:
        return ErrorCode.MEMORY_ERROR
    return ErrorCode.NOT_FOUND


def _json_response(status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None) -> JSONResponse:
    response_headers = {"X-Request-ID": get_request_id() or ""}
    if headers:
        response_headers.update(headers)
    return JSONResponse(status_code=status_code, content=body, headers=response_headers)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_code, body = resolve_exception(exc)
    platform_metrics.record_request(
        latency_ms=0,
        status_code=status_code,
        exception_type=type(exc).__name__,
    )
    return _json_response(status_code, body, headers=dict(exc.headers or {}))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    status_code, body = resolve_exception(exc)
    platform_metrics.record_request(latency_ms=0, status_code=status_code, exception_type="RequestValidationError")
    return _json_response(status_code, body)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception",
        extra_fields={
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(),
        },
    )
    status_code, body = resolve_exception(exc)
    platform_metrics.record_request(
        latency_ms=0,
        status_code=status_code,
        exception_type=type(exc).__name__,
    )
    return _json_response(status_code, body)


def register_exception_handlers(app) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
