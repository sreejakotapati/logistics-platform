"""Standard success-response helpers (the error envelope lives in core.exceptions)."""
from __future__ import annotations

from typing import Any


def ok(data: Any = None, meta: dict | None = None) -> dict:
    body: dict = {"data": data}
    if meta is not None:
        body["meta"] = meta
    return body
