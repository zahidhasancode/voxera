"""One shared HTTP client for voice providers.

Opening a new HTTPS connection for every LLM and TTS request adds a TCP and TLS
handshake to every turn. A shared client keeps connections to the providers
alive between turns.
"""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return the process-wide client, creating it on first use."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=60.0),
        )
    return _client


async def close_http_client() -> None:
    """Close the shared client (called on application shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
