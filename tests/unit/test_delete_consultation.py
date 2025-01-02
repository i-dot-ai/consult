import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import ConsultationWithThemesFactory


@pytest.mark.django_db
def test_delete_consultation():
    consultation = ConsultationWithThemesFactory()

    assert models.Consultation.objects.count() == 1
    assert models.ConsultationResponse.objects.count() >= 1
    assert models.Section.objects.count() >= 1
    assert models.Question.objects.count() >= 1
    assert models.Answer.objects.count() >= 1

    consultation.delete()

    assert models.Consultation.objects.count() == 0
    assert models.ConsultationResponse.objects.count() == 0
    assert models.Section.objects.count() == 0
    assert models.Question.objects.count() == 0
    assert models.Answer.objects.count() == 0
