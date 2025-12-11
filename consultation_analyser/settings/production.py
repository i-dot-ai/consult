import sentry_sdk
from django.conf.global_settings import STORAGES
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat

from consultation_analyser.settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]  # noqa: F405

# Production Database Connection Pooling - Higher limits for scale
DATABASES["default"]["POOL_OPTIONS"].update(  # noqa: F405
    {  # noqa: F405
        "INITIAL_CONNS": env.int("DB_POOL_INITIAL_CONNS", default=10),  # noqa: F405
        "MAX_CONNS": env.int("DB_POOL_MAX_CONNS", default=50),  # noqa: F405
        "MIN_CONNS": env.int("DB_POOL_MIN_CONNS", default=10),  # noqa: F405
        "MAX_SHARED_CONNS": env.int("DB_POOL_MAX_SHARED_CONNS", default=25),  # noqa: F405
        "MAX_OVERFLOW": env.int("DB_POOL_MAX_OVERFLOW", default=25),  # noqa: F405
        "RECYCLE": env.int(  # noqa: F405
            "DB_POOL_RECYCLE", default=1800
        ),  # 30 minutes in production  # noqa: F405
    }
)

SENTRY_DSN = env("SENTRY_DSN")  # noqa: F405
EXECUTION_CONTEXT = env("EXECUTION_CONTEXT")  # noqa: F405
GIT_SHA = env("GIT_SHA")  # noqa: F405


STORAGES["default"] = {  # noqa: F405
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {"bucket_name": env("APP_BUCKET"), "location": "app_data/"},  # noqa: F405
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
