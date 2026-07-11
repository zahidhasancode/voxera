"""Execution guardrails — block dangerous operations."""

import re
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings

_BLOCKED_PATTERNS = (
    re.compile(r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+TABLE\b", re.I),
    re.compile(r"\b(os\.|subprocess|eval|exec|__import__)\b", re.I),
    re.compile(r"\b(rm\s+-rf|/etc/passwd|\.\./)\b", re.I),
)


class ToolGuardrailsValidator:
    """Prevents filesystem, shell, SQL, and prompt-injection patterns."""

    def validate_arguments(self, arguments: dict[str, Any]) -> list[str]:
        violations: list[str] = []
        serialized = str(arguments)
        for pattern in _BLOCKED_PATTERNS:
            if pattern.search(serialized):
                violations.append(f"blocked_pattern: {pattern.pattern}")
        return violations

    def validate_http_url(self, url: str) -> list[str]:
        violations: list[str] = []
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            violations.append("http_url: scheme must be http or https")
            return violations

        host = (parsed.hostname or "").lower()
        allowed = settings.tool_allowed_http_hosts
        if not allowed:
            violations.append("http_url: no allowed hosts configured")
        elif host not in allowed:
            violations.append(f"http_url: host '{host}' not in allowlist")
        return violations

    def validate_tool_slug(self, slug: str, registered_slugs: set[str]) -> list[str]:
        if slug not in registered_slugs:
            return [f"unknown_tool: {slug}"]
        return []
