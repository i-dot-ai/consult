import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from consultation_analyser import factories
from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import Consultation
from consultation_analyser.consultations.urls import urlpatterns

PUBLIC_URL_NAMES = [
    "root",
    "how_it_works",
    "data_sharing",
    "get_involved",
    "privacy",
]
GENERIC_CONSULTATION_URL_NAMES = [
    "consultations",
]
AUTHENTICATION_URL_NAMES = [
    "sign_in",
    "sign_out",
    "magic_link",
]  # No tests - tested elsewhere, all public

REDIRECTING_URL_NAMES = ["show_next_response"]

JSON_SCHEMA_URL_NAMES = ["raw_schema"]

# API endpoints return 403 instead of 404 for unauthenticated users
API_URL_NAMES = [
    "api_demographic_options",
    "api_demographic_aggregations",
    "api_theme_information",
    "api_theme_aggregations",
    "api_filtered_responses",
    "api_question_information",
]

URL_NAMES_TO_EXCLUDE = (
    PUBLIC_URL_NAMES
    + GENERIC_CONSULTATION_URL_NAMES
    + AUTHENTICATION_URL_NAMES
    + REDIRECTING_URL_NAMES
    + JSON_SCHEMA_URL_NAMES
    + API_URL_NAMES
)


@pytest.mark.django_db
def test_access_public_urls_no_login(client):
    for url_name in PUBLIC_URL_NAMES:
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
def test_access_generic_consultation_urls(client):
    for url_name in GENERIC_CONSULTATION_URL_NAMES:
        url = reverse(url_name)
        # No login should give 404
        response = client.get(url)
        assert response.status_code == 404
        # Any logged in user should be able to access pages
        user = factories.UserFactory()
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        client.logout()


def set_up_consultation(user):
    question = factories.QuestionFactory()
    consultation = question.consultation
    consultation.users.add(user)
    consultation.save()

    response = factories.ResponseFactory(question=question)
    factories.ResponseAnnotationFactory(response=response)
    possible_args = {
        "consultation_slug": consultation.slug,
        "question_slug": question.slug,
        "response_id": response.id,
    }
    return possible_args


def set_up_consultation_api(user):
    question = factories.QuestionFactory()
    consultation = question.consultation
    consultation.users.add(user)
    consultation.save()

    response = factories.ResponseFactory(question=question)
    factories.ResponseAnnotationFactory(response=response)
    possible_args = {
        "consultation_pk": consultation.id,
        "question_pk": question.id,
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


@pytest.mark.django_db
def test_consultations_urls_login_required(client):
    """
    This tests all URLs by default unless deliberately excluded (special cases).

    This tests that login is required AND that only users who can see the consultation
    can access pages.

    If you have added a new URL and this test is failing either:
        (1) it should pass and your view is wrong or
        (2) add it as a special case to be excluded and write a separate test.
    """

    user = factories.UserFactory()
    non_consultation_user = factories.UserFactory()
    possible_args = set_up_consultation(user)

    dashboard_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dashboard_access)
    user.save()

    # Get all URLs that haven't explicitly been excluded.
    # Exclude magic links in separate step as potentially more than one.
    url_patterns_excluding_magic_link = [
        url_pattern
        for url_pattern in urlpatterns
        if not str(url_pattern.pattern).startswith("magic-link")
    ]
    url_patterns_to_test = [
        url_pattern
        for url_pattern in url_patterns_excluding_magic_link
        if url_pattern.name not in URL_NAMES_TO_EXCLUDE
    ]

    for url_pattern in url_patterns_to_test:
        url = get_url_for_pattern(url_pattern, possible_args)

        # Not logged in - should 404
        check_expected_status_code(client, url, expected_status_code=404)

        # Logged in with a user for this consultation - 200
        client.force_login(user)
        check_expected_status_code(client, url, 200)
        client.logout()

        # Logged in with a different user - 404
        client.force_login(non_consultation_user)
        check_expected_status_code(client, url, 404)
        client.logout()


# Get API URL patterns
API_URL_PATTERNS = [url_pattern for url_pattern in urlpatterns if url_pattern.name in API_URL_NAMES]


@pytest.mark.django_db
@pytest.mark.parametrize("url_pattern", API_URL_PATTERNS)
def test_api_urls_permission_required(client, url_pattern):
    """
    Test API endpoints return 403 for authentication/permission failures.

    API endpoints use DRF permissions which return 403 (Forbidden) rather than
    404 (Not Found) for unauthorized access.
    """
    user = factories.UserFactory()
    non_consultation_user = factories.UserFactory()
    possible_args = set_up_consultation_api(user)

    dashboard_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dashboard_access)
    user.save()

    url = get_url_for_pattern(url_pattern, possible_args)

    # Not logged in - should return 403 (DRF permission denied)
    check_expected_status_code(client, url, expected_status_code=403)

    # Logged in with a user for this consultation - 200
    client.force_login(user)
    check_expected_status_code(client, url, 200)
    client.logout()

    # Logged in with a different user (no consultation access) - 403
    client.force_login(non_consultation_user)
    check_expected_status_code(client, url, 403)
    client.logout()

    # Logged in with user without dashboard access - 403
    user_no_dashboard = factories.UserFactory()
    # Need to get the consultation from the database to add the user
    consultation = Consultation.objects.get(id=possible_args["consultation_pk"])
    consultation.users.add(user_no_dashboard)
    client.force_login(user_no_dashboard)
    check_expected_status_code(client, url, 403)
    client.logout()


# Get all URLs that haven't explicitly been excluded.
# Exclude magic links in separate step as potentially more than one.
URL_EXCLUDING_MAGIC_LINK = [
    url_pattern
    for url_pattern in urlpatterns
    if str(url_pattern) in REDIRECTING_URL_NAMES
    if not str(url_pattern.pattern).startswith("magic-link")
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_pattern", URL_EXCLUDING_MAGIC_LINK)
def test_urls_permission_required(client, url_pattern):
    """
    Test API endpoints return 403 for authentication/permission failures.
    """
    user = factories.UserFactory()
    non_consultation_user = factories.UserFactory()
    possible_args = set_up_consultation(user)

    dashboard_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dashboard_access)
    user.save()

    url = get_url_for_pattern(url_pattern, possible_args)

    # Not logged in - should 404
    check_expected_status_code(client, url, expected_status_code=404)

    # Logged in with a user for this consultation - 302
    client.force_login(user)
    check_expected_status_code(client, url, 302)
    client.logout()

    # Logged in with a different user - 404
    client.force_login(non_consultation_user)
    check_expected_status_code(client, url, 404)
    client.logout()
