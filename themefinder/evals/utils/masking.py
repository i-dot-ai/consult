"""Redaction for free-text data sent to Langfuse telemetry."""

import re
from typing import Any

_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"(?<!\d)(?:\+|0)[\d ()-]{8,}\d(?!\d)"),
)


def mask_sensitive(data: Any) -> Any:
    if isinstance(data, str):
        for pattern in _PATTERNS:
            data = pattern.sub("[redacted]", data)
        return data
    if isinstance(data, dict):
        return {key: mask_sensitive(value) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return type(data)(mask_sensitive(item) for item in data)
    return data
