"""JWT access and refresh tokens."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import settings
from app.core.exceptions import TokenExpiredError


class TokenService:
    def create_access_token(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None = None,
        role_slug: str | None = None,
        permissions: list[str] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "org": str(organization_id) if organization_id else None,
            "role": role_slug,
            "permissions": permissions or [],
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.IAM_ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

    def create_refresh_token(self, *, user_id: UUID, session_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=settings.IAM_REFRESH_TOKEN_EXPIRE_DAYS),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenExpiredError("Invalid token") from exc
