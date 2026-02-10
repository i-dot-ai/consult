import sentry_sdk
from django.conf.global_settings import STORAGES
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat

from settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]  # noqa: F405


SENTRY_DSN = env("SENTRY_DSN")  # noqa: F405
EXECUTION_CONTEXT = env("EXECUTION_CONTEXT")  # noqa: F405
GIT_SHA = env("GIT_SHA")  # noqa: F405


STORAGES["default"] = {  # noqa: F405
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {"bucket_name": env("AWS_BUCKET_NAME"), "location": "app_data/"},  # noqa: F405
}

STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {"bucket_name": env("AWS_BUCKET_NAME"), "location": "app_data/static/"},  # noqa: F405
}


def sentry_before_send(event, hint):
    """Filters Sentry events before sending.

    Adapted from https://jkfran.com/capturing-unhandled-exceptions-sentry-python/

    This function filters out handled exceptions.

    Args:
        event (dict): The event dictionary containing exception data.

        hint (dict): Additional information about the event, including
            the original exception.

    Returns:
        dict: The modified event dictionary, or None if the event should be
            ignored.
    """
    # Ignore handled exceptions
    exceptions = event.get("exception", {}).get("values", [])
    if exceptions:
        exc = exceptions[-1]
        mechanism = exc.get("mechanism")

        if mechanism:
            if mechanism.get("handled"):
                return None

    return event


sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,  # noqa: F405
    release=GIT_SHA,
    before_send=sentry_before_send,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
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

if env.str("ENVIRONMENT", "prod").lower() != "prod":  # noqa: F405
    INSTALLED_APPS.append("drf_spectacular")  # noqa F405

    REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"  # noqa F405

    # DRF Spectacular settings
    SPECTACULAR_SETTINGS = {
        "TITLE": "Consultation Analyser API",
        "DESCRIPTION": "REST API for the i.AI Consultation Analyser platform",
        "VERSION": "1.0.0",
        "SERVE_INCLUDE_SCHEMA": False,
        "COMPONENT_SPLIT_REQUEST": True,
        "SCHEMA_PATH_PREFIX": "/api/",
    }
