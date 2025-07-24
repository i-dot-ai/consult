import pytest

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import User
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_managing_users_via_support(django_app):
    # given I am an admin user
    user = UserFactory(
        email="email@example.com",
        password="admin",  # pragma: allowlist secret
        is_staff=True,
    )
    sign_in(django_app, user.email)

    users_page = django_app.get("/support/users/")
    assert "email@example.com" in users_page

    # Add a new user
    new_user_page = users_page.click("Add a new user")

    new_user_page.form["email"] = "a-new-user@example.com"
    users_page = new_user_page.form.submit().follow().follow()

    assert "User added" in users_page
    assert "a-new-user@example.com" in users_page

    # Make the new user a staff user and give them dashboard access
    user_page = users_page.click("a-new-user@example.com")
    assert user_page.form["is_staff"].checked is not True
    assert user_page.form["dashboard_access"].checked is not True

    user_page.form["is_staff"] = True
    user_page.form["dashboard_access"] = True

    updated_user_page = user_page.form.submit().follow()
    new_user = User.objects.get(email="a-new-user@example.com")
    assert "User updated" in updated_user_page
    assert user_page.form["is_staff"].checked is True
    assert user_page.form["dashboard_access"].checked is True

    assert new_user.is_staff
    assert new_user.groups.filter(name=DASHBOARD_ACCESS).exists()

    # Now remove dashboard access
    users_page = django_app.get("/support/users/")
    user_page = users_page.click("a-new-user@example.com")

    user_page.form["dashboard_access"] = False
    updated_user_page = user_page.form.submit().follow()
    assert "User updated" in updated_user_page
    assert user_page.form["is_staff"].checked is True
    assert user_page.form["dashboard_access"].checked is False
    new_user = User.objects.get(email="a-new-user@example.com")
    assert not new_user.groups.filter(name=DASHBOARD_ACCESS).exists()

    # Now check we can't remove is_staff for current user
    users_page = django_app.get("/support/users/")
    user_page = users_page.click("email@example.com")

    user_page.form["is_staff"] = False
    failed_user_page = user_page.form.submit()

    assert "You cannot remove admin privileges from your own user" in failed_user_page
    assert user_page.form["dashboard_access"].checked is False
