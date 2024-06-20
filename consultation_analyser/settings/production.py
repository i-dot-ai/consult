import sentry_sdk

from consultation_analyser.settings import base

CSRF_TRUSTED_ORIGINS = ["https://" + base.env("DOMAIN_NAME")]

SENTRY_DSN = base.env("SENTRY_DSN")
EXECUTION_CONTENT = base.env("EXECUTION_CONTENT")
GIT_SHA = base.env("GIT_SHA")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=base.ENVIRONMENT,
    release=GIT_SHA,
)

sentry_sdk.set_tags({"execution_context": EXECUTION_CONTENT})
