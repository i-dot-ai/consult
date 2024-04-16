import pytest

from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_user_can_sign_in(django_app):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    homepage = django_app.get("/")
    homepage.click("Sign in")

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "email@example.com"
    success_page = login_page.form.submit()

    successful_sign_in_page = success_page.click("Click here to sign in")
    homepage = successful_sign_in_page.form.submit().follow()

    signed_out_homepage = homepage.click("Sign out").follow().follow()
    assert "You have signed out" in signed_out_homepage
