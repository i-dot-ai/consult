import pytest
from webtest.app import AppError

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in

SUPPORT_ROUTE = "/support/consultations/"


def assert_expected_menu_items(django_app, endpoint, menu_item):
    response = django_app.get(endpoint)
    response_header = str(response.html.header)
    assert menu_item in response_header


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected_menu_item", ["How it works", "Data sharing", "Get involved", "Sign in"]
)
def test_not_authenticated_navigation(django_app, expected_menu_item):
    assert_expected_menu_items(django_app, "/", expected_menu_item)

    with pytest.raises(AppError):
        assert_expected_menu_items(django_app, SUPPORT_ROUTE, expected_menu_item)


# Non-staff user
@pytest.mark.django_db
@pytest.mark.parametrize("expected_menu_item", ["Your consultations", "Sign out"])
def test_authenticated_navigation(django_app, expected_menu_item):
    UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    sign_in(django_app, "email@example.com")

    with pytest.raises(AppError):
        assert_expected_menu_items(django_app, SUPPORT_ROUTE, expected_menu_item)


@pytest.mark.django_db
@pytest.mark.parametrize("expected_menu_item", ["Consultations", "Users", "Import", "Sign out"])
def test_authenticated_staff_navigation(django_app, expected_menu_item):
    UserFactory(
        email="email@example.com",
        password="admin",  # pragma: allowlist secret`
        is_staff=True,
    )
    sign_in(django_app, "email@example.com")

    assert_expected_menu_items(django_app, SUPPORT_ROUTE, expected_menu_item)
