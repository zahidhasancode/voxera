"""Golden dataset loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def load_golden_dataset(domain: str) -> dict[str, Any]:
    path = GOLDEN_DIR / f"{domain}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Golden dataset not found: {path}")
    return json.loads(path.read_text())


def list_golden_domains() -> list[str]:
    manifest = json.loads((GOLDEN_DIR / "manifest.json").read_text())
    return manifest["domains"]
