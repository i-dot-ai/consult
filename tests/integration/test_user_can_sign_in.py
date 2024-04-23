import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_user_can_sign_in(django_app):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    homepage = django_app.get("/")
    homepage.click("Sign in", index=0)

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "email@example.com"
    success_page = login_page.form.submit()

    successful_sign_in_page = success_page.click("Click here to sign in")
    homepage = successful_sign_in_page.form.submit().follow()

    signed_out_homepage = homepage.click("Sign out", index=0).follow()
    assert "Sign in" in signed_out_homepage
