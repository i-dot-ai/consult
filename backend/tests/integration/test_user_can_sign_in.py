import pytest
from django.core import mail

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_user_can_sign_in(django_app):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "invalid@example.com"
    login_page.form.submit()

    # assert we never sent a magic link
    assert len(mail.outbox) == 0

    # sign-in steps are defined in this helper function
    homepage = sign_in(django_app, "email@example.com")

    login_page = django_app.get("/sign-in/")
    assert login_page.status_code == 302

    signed_out_homepage = homepage.click("Sign out", index=0).follow()
    assert "Sign in" in signed_out_homepage
