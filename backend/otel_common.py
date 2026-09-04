"""Shared gate for the OTel helpers."""

from __future__ import annotations

from django.conf import settings


def otel_requested() -> bool:
    return bool(settings.OTEL_ENABLED)
