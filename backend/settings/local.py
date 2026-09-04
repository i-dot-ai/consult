from django.conf.global_settings import STORAGES

from settings.base import *

INSTALLED_APPS.append("django_extensions")
INSTALLED_APPS.append("drf_spectacular")

STORAGES["default"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": BASE_DIR / "tmp"},
}

REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Consultation Analyser API",
    "DESCRIPTION": "REST API for the i.AI Consultation Analyser platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
}
