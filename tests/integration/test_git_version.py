import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(GIT_SHA="12345678abcdefghijklmnoprstuvwxyz")  # pragma: allowlist secret
def test_git_version_displayed_from_env(django_app):
    homepage = django_app.get("/")
    assert "Version: 12345678" in homepage


@pytest.mark.django_db
@override_settings(GIT_SHA=None)
def test_default_to_local(django_app):
    homepage = django_app.get("/")
    assert "Version:" not in homepage
