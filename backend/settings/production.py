import sentry_sdk
from django.conf.global_settings import STORAGES
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat

from otel_bootstrap import bootstrap_otel
from otel_django import configure_django_otel
from sentry_context import default_perf_sample_rate, sentry_before_send
from settings.base import *

CSRF_TRUSTED_ORIGINS = TRUSTED_ORIGINS


SENTRY_DSN = env("SENTRY_DSN")
# Re-read with no default on purpose: in deployed envs Terraform sets this per runtime,
# so a missing value is a misconfiguration we want to fail loudly on rather than mask.
EXECUTION_CONTEXT = env("EXECUTION_CONTEXT")


STORAGES["default"] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {"bucket_name": env("AWS_BUCKET_NAME"), "location": "app_data/"},
}

STORAGES["staticfiles"] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {"bucket_name": env("AWS_BUCKET_NAME"), "location": "app_data/static/"},
}


_perf_sample_rate = default_perf_sample_rate(ENVIRONMENT)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
    before_send=sentry_before_send,
    traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=_perf_sample_rate),
    profile_session_sample_rate=env.float(
        "SENTRY_PROFILE_SESSION_SAMPLE_RATE", default=_perf_sample_rate
    ),
    profile_lifecycle="trace",
    release=SENTRY_RELEASE,
)


sentry_sdk.set_tags({"execution_context": EXECUTION_CONTEXT})


LOGGER = StructuredLogger(
    level="info",
    options={
        "execution_environment": ExecutionEnvironmentType.FARGATE,
        "log_format": LogOutputFormat.JSON,
        "ship_logs": True,
    },
)
LOGGER.set_context_field("execution_context", EXECUTION_CONTEXT)


if OTEL_ENABLED:
    # No defaults: Terraform sets these per runtime, so a missing value is a
    # misconfiguration we fail loudly on rather than silently disabling telemetry.
    OTEL_EXPORTER_OTLP_ENDPOINT = env("OTEL_EXPORTER_OTLP_ENDPOINT")
    OTEL_SERVICE_NAME = env("OTEL_SERVICE_NAME")
    if EXECUTION_CONTEXT == "worker":
        bootstrap_otel(logger=LOGGER, service_name=OTEL_SERVICE_NAME)
    else:
        configure_django_otel(logger=LOGGER, service_name=OTEL_SERVICE_NAME)


if env.str("ENVIRONMENT", "prod").lower() != "prod":
    INSTALLED_APPS.append("drf_spectacular")

    REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"

    # DRF Spectacular settings
    SPECTACULAR_SETTINGS = {
        "TITLE": "Consultation Analyser API",
        "DESCRIPTION": "REST API for the i.AI Consultation Analyser platform",
        "VERSION": "1.0.0",
        "SERVE_INCLUDE_SCHEMA": False,
        "COMPONENT_SPLIT_REQUEST": True,
        "SCHEMA_PATH_PREFIX": "/api/",
    }
