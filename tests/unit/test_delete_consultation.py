import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_delete_consultation():
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(consultation=consultation)
    respondent = factories.RespondentFactory(consultation=consultation)
    factories.ResponseFactory(respondent=respondent, question=question)

    assert models.Consultation.objects.count() == 1
    assert models.Respondent.objects.count() == 1
    assert models.Question.objects.count() == 1
    assert models.Response.objects.count() == 1

    consultation.delete()

    assert models.Consultation.objects.count() == 0
    assert models.Respondent.objects.count() == 0
    assert models.Question.objects.count() == 0
    assert models.Response.objects.count() == 0
