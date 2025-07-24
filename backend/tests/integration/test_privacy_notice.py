import pytest


@pytest.mark.django_db
def test_privacy_notice(django_app):
    homepage = django_app.get("/")
    privacy_page = homepage.click("Privacy notice")
    assert "Privacy notice" in privacy_page
