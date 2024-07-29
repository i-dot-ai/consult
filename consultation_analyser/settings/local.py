from consultation_analyser.settings.base import *  # noqa
from django.conf.global_settings import STORAGES

INSTALLED_APPS.append("django_extensions")  # noqa F405

STORAGES["default"] = {  # noqa
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {
        "location": BASE_DIR / "tmp"  # noqa
    },
}
