import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_consultation_save_unique_slugs():
    consultation_title = "My First Consultation"
    slugified = "my-first-consultation"
    consultation = ConsultationFactory(title=consultation_title)
    assert consultation.slug == slugified
    another_consultation = ConsultationFactory(title=consultation_title)
    assert another_consultation.slug != consultation.slug
    assert another_consultation.slug == f"{slugified}-1"
    yet_another_consultation = ConsultationFactory(title=consultation_title)
    assert yet_another_consultation.slug != consultation.slug
    assert yet_another_consultation.slug == f"{slugified}-2"



@pytest.mark.django_db
def test_consultation_save_update_slugs():
    consultation_title = "My First Consultation"
    consultation = ConsultationFactory(title=consultation_title)
    assert consultation.slug == "my-first-consultation"
    consultation.title = "My Second Consultation"
    consultation.save()
    assert consultation.slug == "my-second-consultation"
