import sentry_sdk

from consultation_analyser.settings.base import *, env # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]

SENTRY_DSN = env("SENTRY_DSN")
EXECUTION_CONTENT = env("EXECUTION_CONTENT")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
)

sentry_sdk.set_tags({"execution_context": EXECUTION_CONTENT})
