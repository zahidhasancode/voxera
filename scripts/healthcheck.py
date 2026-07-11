#!/usr/bin/env python3
"""Container health check — probes readiness endpoint."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/health/ready")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    try:
        req = urllib.request.Request(args.url, method="GET")
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            if resp.status >= 500:
                return 1
            return 0
    except urllib.error.HTTPError as exc:
        return 0 if exc.code < 500 else 1
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
