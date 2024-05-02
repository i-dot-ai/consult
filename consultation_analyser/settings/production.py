import sentry_sdk

from consultation_analyser.settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]

SENTRY_DSN = env("SENTRY_DSN")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
)
