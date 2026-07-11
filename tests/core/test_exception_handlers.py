"""Exception handler tests."""

import pytest
from fastapi import HTTPException, status

from app.core.errors import ErrorCode
from app.core.exception_handlers import resolve_exception
from app.core.exceptions import NotFoundError, ToolRateLimitError, InvalidCredentialsError


def test_resolve_not_found():
    status_code, body = resolve_exception(NotFoundError("missing"))
    assert status_code == status.HTTP_404_NOT_FOUND
    assert body["success"] is False
    assert body["error"]["code"] == ErrorCode.NOT_FOUND


def test_resolve_auth_error():
    status_code, body = resolve_exception(InvalidCredentialsError("bad creds"))
    assert status_code == status.HTTP_401_UNAUTHORIZED
    assert body["error"]["code"] == ErrorCode.AUTHENTICATION_ERROR


def test_resolve_rate_limit():
    status_code, body = resolve_exception(ToolRateLimitError("slow down"))
    assert status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert body["error"]["code"] == ErrorCode.RATE_LIMIT_EXCEEDED


def test_resolve_preformatted_http_exception():
    envelope = {
        "success": False,
        "error": {
            "code": "validation_error",
            "message": "bad",
            "details": None,
            "request_id": "abc",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "documentation_url": "https://docs.voxera.ai/errors/validation_error",
        },
    }
    status_code, body = resolve_exception(HTTPException(status_code=422, detail=envelope))
    assert status_code == 422
    assert body == envelope


def test_resolve_unknown_exception():
    status_code, body = resolve_exception(RuntimeError("boom"))
    assert status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert body["error"]["code"] == ErrorCode.INTERNAL_ERROR
    assert "stack" not in str(body).lower()
