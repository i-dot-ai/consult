from consultation_analyser.settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]
