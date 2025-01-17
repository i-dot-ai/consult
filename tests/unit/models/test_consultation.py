import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_consultation_save():
    consultation_title = "My First Consultation"
    slugified = "my-first-consultation"
    consultation = ConsultationFactory(text=consultation_title)
    assert consultation.slug == slugified
    another_consultation = ConsultationFactory(text=consultation_title)
    assert another_consultation.slug != consultation.slug
    assert another_consultation.slug == f"{slugified}-1"
    yet_another_consultation = ConsultationFactory(text=consultation_title)
    assert yet_another_consultation.slug != consultation.slug
    assert yet_another_consultation.slug == f"{slugified}-2"

