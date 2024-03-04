import environ

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env.test"))

from consultation_analyser.settings.base import *  # noqa
