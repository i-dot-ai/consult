import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
@override_switch("CONSULTATION_PROCESSING", True)
def test_accessing_when_flag_is_on(client):
    consultation = ConsultationFactory()
    assert client.get("/").status_code == 200
    assert client.get(f"/consultations/{consultation.slug}/").status_code == 200


@pytest.mark.django_db
@override_switch("CONSULTATION_PROCESSING", False)
def test_accessing_when_flag_is_off(client):
    consultation = ConsultationFactory()
    assert client.get("/").status_code == 200
    assert client.get(f"/consultations/{consultation.slug}/").status_code == 404
