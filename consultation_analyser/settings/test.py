import os
from pathlib import Path

import environ
from django.conf.global_settings import STORAGES

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env.test"))

from consultation_analyser.settings.base import *  # noqa

STORAGES["default"] = {
    "BACKEND": "django.core.files.storage.InMemoryStorage",
}

# process all async jobs inline for testing
Q_CLUSTER["sync"] = True  # noqa

# Use memory email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
