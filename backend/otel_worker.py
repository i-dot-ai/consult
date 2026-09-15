from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

from django.conf import settings
from i_dot_ai_utilities.logging.otel import (
    configure_otel,
    ensure_structlog_otel_processors,
    force_flush_otel,
)
from opentelemetry import trace


def configure_worker_otel(*, logger, service_name: str) -> None:
    try:
        configure_otel(service_name=service_name)
        ensure_structlog_otel_processors()
    except Exception:  # noqa: BLE001 - telemetry setup must never block the worker
        logger.warning(
            "OTel setup failed; telemetry disabled for {service_name}",
            service_name=service_name,
        )


@contextlib.contextmanager
def execution_span(
    name: str, *, context_id: str | None = None, **attributes: Any
) -> Iterator[None]:
    """Wrap a unit of work in a span, carrying context_id so logs correlate."""
    if not settings.OTEL_CONFIGURED:
        yield
        return

    tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)
    with tracer.start_as_current_span(name) as span:
        if context_id:
            span.set_attribute("context_id", context_id)
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield


def flush_otel() -> None:
    """Flush pending telemetry at a job boundary."""
    if not settings.OTEL_CONFIGURED:
        return
    force_flush_otel()
