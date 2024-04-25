import re

import pytest
from django.core import mail
from waffle.testutils import override_switch

from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_user_can_sign_in(django_app):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    homepage = django_app.get("/")
    homepage.click("Sign in", index=0)

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "invalid@example.com"
    login_page.form.submit()

    assert len(mail.outbox) == 0

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "email@example.com"
    login_page.form.submit()

    sign_in_email = mail.outbox[0]

    assert sign_in_email.subject == "Sign in to Consultation analyser"
    url = re.search("(?P<url>https?://\\S+)", sign_in_email.body).group("url")

    successful_sign_in_page = django_app.get(url)
    homepage = successful_sign_in_page.form.submit().follow()

    signed_out_homepage = homepage.click("Sign out", index=0).follow()
    assert "Sign in" in signed_out_homepage
