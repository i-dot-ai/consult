import importlib

import pytest
from django.conf import settings
from django.urls import clear_url_caches


@pytest.fixture
def reload_urlconf():
    """Reload the root URLconf so a DATA_SETUP_V2_ENABLED override takes effect.

    The v2 include is decided at URLconf import time, so override_settings alone
    won't add or drop the routes without rebuilding the resolver.
    """

    def _reload():
        clear_url_caches()
        importlib.reload(importlib.import_module(settings.ROOT_URLCONF))

    yield _reload
    _reload()
