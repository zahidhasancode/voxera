"""Authentication middleware path rules."""

from app.iam.middleware.authentication import AuthenticationMiddleware


def test_public_login_route():
    middleware = AuthenticationMiddleware(None)
    assert middleware._is_public("POST", "/api/v1/iam/auth/login")


def test_public_register_route():
    middleware = AuthenticationMiddleware(None)
    assert middleware._is_public("POST", "/api/v1/iam/auth/register")


def test_public_health_route():
    middleware = AuthenticationMiddleware(None)
    assert middleware._is_public("GET", "/api/v1/health")


def test_protected_tenant_route():
    middleware = AuthenticationMiddleware(None)
    assert not middleware._is_public("GET", "/api/v1/tenants/00000000-0000-0000-0000-000000000001/agents")
