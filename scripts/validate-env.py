#!/usr/bin/env python3
"""Validate required environment variables before startup (fail fast)."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from app.core.config import settings

        settings.validate_security_settings()

        if settings.is_production or settings.is_staging:
            missing: list[str] = []
            if settings.database_enabled and not settings.DATABASE_URL:
                missing.append("DATABASE_URL")
            if settings.VOICE_REQUIRE_PROVIDERS:
                for name in ("STT_PROVIDER", "LLM_PROVIDER", "TTS_PROVIDER"):
                    if not getattr(settings, name):
                        missing.append(name)
            if missing:
                print(f"ERROR: Missing required configuration: {', '.join(missing)}", file=sys.stderr)
                return 1

        print(f"OK: configuration valid for environment={settings.ENVIRONMENT}")
        return 0
    except Exception as exc:
        print(f"ERROR: configuration validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
