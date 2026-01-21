import pytest
from django.urls import reverse
from tests.utils import build_url

from backend import factories
from backend.consultations.urls import urlpatterns

PUBLIC_URL_NAMES = ["git-sha"]
AUTHENTICATION_URL_NAMES = [
    "sign_in",
    "sign_out",
    "magic_link",
]  # No tests - tested elsewhere, all public

JSON_SCHEMA_URL_NAMES = ["raw_schema"]

# API endpoints return 403 instead of 404 for unauthenticated users
API_URL_NAMES = [
    "consultations-demographic-options",
    "response-demographic-aggregations",
    "question-theme-information",
    "response-theme-aggregations",
    "response-list",
    "question-detail",
]

URL_NAMES_TO_EXCLUDE = (
    PUBLIC_URL_NAMES + AUTHENTICATION_URL_NAMES + JSON_SCHEMA_URL_NAMES + API_URL_NAMES
)


@pytest.mark.django_db
def test_access_public_urls_no_login(client):
    for url_name in PUBLIC_URL_NAMES:
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 200


def set_up_consultation(user, free_text_question):
    consultation = free_text_question.consultation
    consultation.users.add(user)
    consultation.save()

    response = factories.ResponseFactory(question=free_text_question)
    factories.ResponseAnnotationFactory(response=response)
    possible_args = {
        "consultation_id": consultation.id,
        "question_id": free_text_question.id,
        "response_id": response.id,
    }
    return possible_args


def check_expected_status_code(client, url, expected_status_code):
    response = client.get(url)
    assert response.status_code == expected_status_code


def get_url_for_pattern(url_pattern, possible_args):
    # Get a dictionary of any args that might occur
    url_str = str(url_pattern)
    kwargs = {}
    for key in possible_args:
        if key in url_str:
            kwargs[key] = possible_args[key]
    url = reverse(url_pattern.name, kwargs=kwargs)
    return url


# Get all URLs that haven't explicitly been excluded.
# Exclude magic links in separate step as potentially more than one.
api_url_patterns = [
    url_pattern for url_pattern in urlpatterns if not str(url_pattern.pattern).startswith("api")
]
url_patterns_to_test = [
    url_pattern for url_pattern in api_url_patterns if url_pattern.name not in URL_NAMES_TO_EXCLUDE
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_pattern", url_patterns_to_test)
def test_consultations_urls_login_required(
    client,
    free_text_question,
    non_consultation_user,
    dashboard_user,
    url_pattern,
):
    """
    This tests all URLs by default unless deliberately excluded (special cases).

    This tests that login is required AND that only users who can see the consultation
    can access pages.

    If you have added a new URL and this test is failing either:
        (1) it should pass and your view is wrong or
        (2) add it as a special case to be excluded and write a separate test.
    """

    possible_args = set_up_consultation(dashboard_user, free_text_question)

    url = get_url_for_pattern(url_pattern, possible_args)

    # Not logged in - should 404
    check_expected_status_code(client, url, expected_status_code=404)

    # Logged in with a user for this consultation - 200
    client.force_login(dashboard_user)
    check_expected_status_code(client, url, 200)
    client.logout()

    # Logged in with a different user - 404
    client.force_login(non_consultation_user)
    check_expected_status_code(client, url, 404)
    client.logout()


@pytest.mark.django_db
@pytest.mark.parametrize("url_pattern", API_URL_NAMES)
def test_api_urls_permission_required(
    client, free_text_question, dashboard_user, non_consultation_user, url_pattern
):
    """
    Test API endpoints return 403 for authentication/permission failures.

    API endpoints use DRF permissions which return 403 (Forbidden) rather than
    404 (Not Found) for unauthorized access.
    """

    response = factories.ResponseFactory(question=free_text_question)
    factories.ResponseAnnotationFactory(response=response)

    url = build_url(url_pattern, free_text_question)

    # Not logged in - should return 401 (DRF un-authenticated)
    check_expected_status_code(client, url, expected_status_code=401)

    # Logged in with a user for this consultation - 200
    client.force_login(dashboard_user)
    check_expected_status_code(client, url, 200)
    client.logout()

    # Logged in with a different user (no consultation access) - 403
    client.force_login(non_consultation_user)
    check_expected_status_code(client, url, 403)
    client.logout()

    # Logged in with user without dashboard access - 403
    # user_no_dashboard = factories.UserFactory()
    # Need to get the consultation from the database to add the user
    # free_text_question.consultation.users.add(user_no_dashboard)
    # client.force_login(user_no_dashboard)
    # check_expected_status_code(client, url, 403)
    # client.logout()


@pytest.mark.django_db
@pytest.mark.parametrize("url_pattern", url_patterns_to_test)
def test_urls_permission_required(
    client, free_text_question, non_consultation_user, dashboard_user, url_pattern
):
    """
    Test API endpoints return 403 for authentication/permission failures.
    """
    possible_args = set_up_consultation(dashboard_user, free_text_question)

    url = get_url_for_pattern(url_pattern, possible_args)

    # Not logged in - should 404
    check_expected_status_code(client, url, expected_status_code=404)

    # Logged in with a user for this consultation - 302
    client.force_login(dashboard_user)
    check_expected_status_code(client, url, 302)
    client.logout()

    # Logged in with a different user - 404
    client.force_login(non_consultation_user)
    check_expected_status_code(client, url, 404)
    client.logout()
