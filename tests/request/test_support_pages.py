import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_no_login_support_pages(client):
    consultation = ConsultationFactory()
    support_urls = [
        "",
        "sign-out/",
        "consultations/",
        f"consultations/{consultation.id}/",
    ]
    for url in support_urls:
        full_url = f"/support/{url}"
        response = client.get(full_url)
        assert response.status_code == 404  # No access - 404
