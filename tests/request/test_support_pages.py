import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "status_code"),
    [
        ("/support/", 403),  # Forbidden
        ("/support/sign-out/", 404),  # Not Found
        ("/support/consultations/", 403),  # Forbidden
        ("/support/consultations/{consultation_id}/", 403),  # Forbidden
    ],
)
def test_no_login_support_pages(client, consultation, url, status_code):
    full_url = url.format(consultation_id=consultation.id)
    response = client.get(full_url)
    assert response.status_code == status_code
