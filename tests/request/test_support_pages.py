import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "expected_status_code"),
    [
        ("/support/", 403),  # Permission Denied
        ("/support/sign-out/", 404),  # Not Found
        ("/support/consultations/", 403),  # Permission Denied
        ("/support/consultations/{consultation_id}/", 403),  # Permission Denied
    ],
)
def test_no_login_support_pages(client, consultation, url, expected_status_code):
    full_url = url.format(consultation_id=consultation.id)
    response = client.get(full_url)
    assert response.status_code == expected_status_code
