"""Process-level OpenTelemetry bootstrap for the RQ worker."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

from i_dot_ai_utilities.logging._otel import (
    configure_otel,
    ensure_structlog_otel_processors,
    force_flush_otel,
)
from opentelemetry import trace

from otel_common import otel_requested


def bootstrap_otel(*, logger, service_name: str) -> None:
    # No otel_requested() self-guard here (unlike execution_span/flush_otel): this runs
    # at settings-import time before django.conf.settings is ready, so the caller gates it.
    try:
        configure_otel(service_name=service_name)
        ensure_structlog_otel_processors()
    except Exception:  # noqa: BLE001 - telemetry setup must never block the worker
        logger.warning(
            "OTel setup failed; telemetry disabled for {service_name}",
            service_name=service_name,
        )


@contextlib.contextmanager
def execution_span(name: str, *, context_id: str | None = None, **attributes: Any) -> Iterator[None]:
    """Wrap a unit of work in a span, carrying context_id so logs correlate."""
    if not otel_requested():
        yield
        return

    tracer = trace.get_tracer("consult-worker")
    with tracer.start_as_current_span(name) as span:
        if context_id:
            span.set_attribute("context_id", context_id)
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield


def flush_otel() -> None:
    """Flush pending telemetry at a job boundary."""
    if not otel_requested():
        return
    force_flush_otel()
