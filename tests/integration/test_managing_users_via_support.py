import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_managin_users_via_support(django_app):
    # given I am an admin user
    user = UserFactory(email="email@example.com", password="admin", is_staff=True)  # pragma: allowlist secret
    sign_in(django_app, user.email)

    users_page = django_app.get("/support/users/")

    assert "email@example.com" in users_page

    new_user_page = users_page.click("Add a new user")

    new_user_page.form["email"] = "a-new-user@example.com"
    users_page = new_user_page.form.submit().follow().follow()

    assert "User added" in users_page
    assert "a-new-user@example.com" in users_page
