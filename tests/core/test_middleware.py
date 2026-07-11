"""Request context middleware tests."""

from app.core.errors import build_error_response
from app.core.logger import get_request_id, set_request_id


def test_error_response_includes_request_id():
    set_request_id("req-123")
    body = build_error_response(code="internal_error", message="failed")
    assert body["error"]["request_id"] == "req-123"
    assert body["success"] is False
    assert "timestamp" in body["error"]
    assert "documentation_url" in body["error"]
