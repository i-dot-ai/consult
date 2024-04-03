import pytest
from django_webtest import WebTestMixin


class MixinWithInstanceVariablesAndAuthDisabled(WebTestMixin):
    """
    Copy this straight out of django-webtest but change the value of setup_auth
    to false until we've got auth configured
    """

    def __init__(self):
        self.extra_environ = {}
        self.csrf_checks = True
        self.setup_auth = False


@pytest.fixture(scope="session")
def django_app_mixin():
    app_mixin = MixinWithInstanceVariablesAndAuthDisabled()
    return app_mixin
