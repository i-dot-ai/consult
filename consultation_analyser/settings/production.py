import sentry_sdk

from consultation_analyser.settings.base import * # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]

SENTRY_DSN = env("SENTRY_DSN")
EXECUTION_CONTEXT = env("EXECUTION_CONTEXT")
GIT_SHA = env("GIT_SHA")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
    release=GIT_SHA,
)

sentry_sdk.set_tags({"execution_context": EXECUTION_CONTEXT})
