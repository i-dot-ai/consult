import os
from pathlib import Path

import environ
from django.conf.global_settings import STORAGES

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env.test file
environ.Env.read_env(os.path.join(BASE_DIR, ".env.test"))

from settings.base import *

OTEL_EXPORTER_OTLP_ENDPOINT = "http://collector-test:4317"
OTEL_SERVICE_NAME = "consult-backend-test"

STORAGES["default"] = {
    "BACKEND": "django.core.files.storage.InMemoryStorage",
}

# process all async jobs inline
for queueConfig in RQ_QUEUES.values():
    queueConfig["ASYNC"] = False

# Use memory email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

INSTALLED_APPS.append("drf_spectacular")

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
