from django.conf.global_settings import STORAGES

from consultation_analyser.settings.base import *  # noqa

INSTALLED_APPS.append("django_extensions")  # noqa F405
INSTALLED_APPS.append("pyflame")  # noqa F405

STORAGES["default"] = {  # noqa
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {
        "location": BASE_DIR / "tmp"  # noqa
    },
}

SIGNIN_URL = "http://" + DOMAIN_NAME + ":3000" + LOGIN_URL  # noqa: F405
