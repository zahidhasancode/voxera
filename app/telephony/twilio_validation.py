"""Twilio webhook signature validation."""

from __future__ import annotations

import base64
import hashlib
import hmac
from urllib.parse import urljoin

from fastapi import HTTPException, Request, status

from app.core.config import settings


def _build_validation_url(request: Request) -> str:
    base = (settings.TWILIO_PUBLIC_BASE_URL or "").strip().rstrip("/")
    if base:
        if not base.startswith("http"):
            base = f"https://{base}"
        return urljoin(f"{base}/", request.url.path.lstrip("/"))
    return str(request.url)


async def require_twilio_signature(request: Request) -> dict[str, str]:
    """FastAPI dependency validating X-Twilio-Signature and returning form fields."""
    auth_token = (settings.TWILIO_AUTH_TOKEN or "").strip()
    form = await request.form()
    fields = {k: v for k, v in form.multi_items()}

    if not auth_token:
        if settings.is_production or settings.is_staging:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio signature validation is not configured",
            )
        return fields

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Twilio signature",
        )

    params = sorted(form.multi_items())
    url = _build_validation_url(request)
    data = url + "".join(f"{k}{v}" for k, v in params)
    digest = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("utf-8")

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )

    return fields
