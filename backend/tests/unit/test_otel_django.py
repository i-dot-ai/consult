import json
import os
from unittest.mock import MagicMock, patch

from i_dot_ai_utilities.logging._otel import setup as otel_setup
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import otel_django


def test_configure_warns_and_continues_when_setup_fails():
    logger = MagicMock()
    with patch.object(otel_django, "configure_otel_for_django", side_effect=RuntimeError("boom")):
        otel_django.configure_django_otel(logger=logger, service_name="consult-backend-test")
    logger.warning.assert_called_once()
    assert logger.warning.call_args.kwargs["service_name"] == "consult-backend-test"


def test_enabled_correlates_existing_logs_with_the_active_span(settings, reset_otel, capsys):
    exporter = InMemorySpanExporter()

    # Construct the logger first: StructuredLogger resets structlog config, and
    # configure has to re-insert the trace processor afterwards for this to pass.
    logger = StructuredLogger(
        level="info",
        options={
            "execution_environment": ExecutionEnvironmentType.LOCAL,
            "log_format": LogOutputFormat.JSON,
        },
    )

    with (
        patch.dict(
            os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": settings.OTEL_EXPORTER_OTLP_ENDPOINT}
        ),
        patch.object(otel_setup, "_default_otlp_span_exporter", lambda: exporter),
    ):
        otel_django.configure_django_otel(logger=logger, service_name=settings.OTEL_SERVICE_NAME)
        assert isinstance(trace.get_tracer_provider(), TracerProvider)

        with trace.get_tracer("test").start_as_current_span("request"):
            logger.info("handled request")

        trace.get_tracer_provider().force_flush()
        spans = exporter.get_finished_spans()

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    logged = next(e for e in events if e.get("message") == "handled request")

    assert len(logged["trace_id"]) == 32
    assert len(logged["span_id"]) == 16

    assert spans, "the active span should be recorded and exported"
    assert format(spans[0].context.trace_id, "032x") == logged["trace_id"]
