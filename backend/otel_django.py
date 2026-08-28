"""OpenTelemetry bootstrap for the Django request path."""

from __future__ import annotations

from i_dot_ai_utilities.logging._otel import (
    configure_otel_for_django,
    ensure_structlog_otel_processors,
)


def configure_django_otel(*, logger, service_name: str) -> None:
    try:
        # StructuredLogger is built during settings import, so restore its
        # processors after instrumenting or logs ship without trace ids.
        configure_otel_for_django(service_name=service_name)
        ensure_structlog_otel_processors()
    except Exception:  # noqa: BLE001 - telemetry setup must never block app startup
        logger.warning(
            "OTel setup failed; telemetry disabled for {service_name}",
            service_name=service_name,
        )
