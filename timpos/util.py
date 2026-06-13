"""Shared deterministic helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def deterministic_id(prefix: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}.{digest}"
