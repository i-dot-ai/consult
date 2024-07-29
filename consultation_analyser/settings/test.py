import os
from pathlib import Path

from django.conf.global_settings import STORAGES

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env.test"))

from consultation_analyser.settings.base import *  # noqa

STORAGES["default"] = {
    "BACKEND": "django.core.files.storage.InMemoryStorage",
}
