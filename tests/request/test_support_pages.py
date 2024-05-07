import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_no_login_support_pages(client):
    ConsultationFactory(slug="consultation-slug")
    support_urls = [
        "",
        "sign-out/",
        "consultations/",
        "consultations/consultation-slug/",
    ]
    for url in support_urls:
        full_url = f"/support/{url}"
        response = client.get(full_url)
        assert response.status_code == 302  # No access, redirect to admin login
