"""Process-level OpenTelemetry bootstrap for the RQ worker.

Dormant until OTEL_ENABLED is on, a collector endpoint is set, and the util's
[otel] extra is installed; a no-op otherwise so the worker keeps running on the
existing StructuredLogger.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from typing import Any

from django.conf import settings

OTEL_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_ENDPOINT"
OTEL_ENABLED_ENV = "OTEL_ENABLED"
_TRACER_NAME = "consult.worker"


def otel_requested() -> bool:
    """Bootstrap only when the flag is on and a collector endpoint is configured."""
    enabled = os.environ.get(OTEL_ENABLED_ENV, "").strip().lower() == "true"
    return enabled and bool(os.environ.get(OTEL_ENDPOINT_ENV))


def bootstrap_otel(service_name: str) -> None:
    """Configure OTel for a long-lived worker process. No-op unless requested."""
    if not otel_requested():
        return

    logger = settings.LOGGER
    try:
        from i_dot_ai_utilities.logging._otel import (
            configure_otel,
            ensure_structlog_otel_processors,
        )
    except ImportError:
        logger.warning(
            "OTel endpoint is set but the i-dot-ai-utilities [otel] extra is not "
            "installed; telemetry disabled for {service_name}",
            service_name=service_name,
        )
        return

    try:
        configure_otel(service_name=service_name)
        ensure_structlog_otel_processors()
    except RuntimeError:
        logger.warning(
            "OTel endpoint is set but the exporter is unavailable; telemetry "
            "disabled for {service_name}",
            service_name=service_name,
        )


@contextlib.contextmanager
def execution_span(name: str, *, context_id: str | None = None, **attributes: Any) -> Iterator[None]:
    """Wrap a unit of work in a span, carrying context_id so logs correlate.

    A no-op that just runs the body when OTel isn't configured.
    """
    if not otel_requested():
        yield
        return
    try:
        from opentelemetry import trace
    except ImportError:
        yield
        return

    tracer = trace.get_tracer(_TRACER_NAME)
    with tracer.start_as_current_span(name) as span:
        if context_id:
            span.set_attribute("context_id", context_id)
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield


def flush_otel() -> None:
    """Flush pending telemetry at a job boundary. No-op unless requested."""
    if not otel_requested():
        return
    try:
        from i_dot_ai_utilities.logging._otel import force_flush_otel
    except ImportError:
        return
    force_flush_otel()
