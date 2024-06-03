import sentry_sdk

from consultation_analyser.settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]  # noqa: F405

SENTRY_DSN = env("SENTRY_DSN")  # noqa: F405

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,  # noqa: F405
)
