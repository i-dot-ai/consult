import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/support/",
        "/support/sign-out/",
        "/support/consultations/",
        "/support/consultations/{consultation_id}/",
    ],
)
def test_no_login_support_pages(client, consultation, url):
    full_url = url.format(consultation_id=consultation.id)
    response = client.get(full_url)
    assert response.status_code == 302
    assert response.url.endswith("/accounts/oidc/gds/login/")
