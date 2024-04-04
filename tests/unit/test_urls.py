import pytest

from consultation_analyser.consultations.factories import ConsultationFactory


def test_batch_example(client):
    response = client.get("/batch-example")
    assert response.status_code == 200


def test_consultation_example(client):
    response = client.get("/consultation-example")
    assert response.status_code == 200


@pytest.mark.django_db
def test_show_consultation(client):
    consultation = ConsultationFactory()
    response = client.get(f"/consultations/{consultation.slug}")
    assert response.status_code == 200
