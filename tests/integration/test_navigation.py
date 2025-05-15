import pytest
from webtest.app import AppError

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in

CONSULTATIONS_ROUTE = "/consultations/"
SUPPORT_ROUTE = "/support/consultations/"


def assert_expected_menu_items(django_app, endpoint, menu_items):
    response = django_app.get(endpoint)
    response_header = str(response.html.header)

    for menu_item in menu_items:
        assert menu_item in response_header


def test_not_authenticated_navigation(django_app):
    expected_menu_items = ["How it works", "Data sharing", "Get involved", "Sign in"]

    assert_expected_menu_items(django_app, "/", expected_menu_items)

    with pytest.raises(AppError):  # expect a 404 response
        assert_expected_menu_items(django_app, CONSULTATIONS_ROUTE, expected_menu_items)

    with pytest.raises(AppError):
        assert_expected_menu_items(django_app, SUPPORT_ROUTE, expected_menu_items)


# Non-staff user
@pytest.mark.django_db
def test_authenticated_navigation(django_app):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    sign_in(django_app, "email@example.com")

    expected_menu_items = ["Your consultations", "Sign out"]

    assert_expected_menu_items(django_app, CONSULTATIONS_ROUTE, expected_menu_items)

    with pytest.raises(AppError):
        assert_expected_menu_items(django_app, SUPPORT_ROUTE, expected_menu_items)


@pytest.mark.django_db
def test_authenticated_staff_navigation(django_app):
    UserFactory(
        email="email@example.com", password="admin", is_staff=True # pragma: allowlist secret`
    )
    sign_in(django_app, "email@example.com")

    assert_expected_menu_items(
        django_app, CONSULTATIONS_ROUTE, ["Support", "Your consultations", "Sign out"]
    )

    assert_expected_menu_items(
        django_app, SUPPORT_ROUTE, ["Consultations", "Users", "Import", "Sign out"]
    )
