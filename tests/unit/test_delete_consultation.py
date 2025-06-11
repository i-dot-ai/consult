import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.skip(reason="Doesn't work whilst in the middle of model changes")
@pytest.mark.django_db
def test_delete_consultation():
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(consultation=consultation)
    question_part = factories.FreeTextQuestionPartFactory(question=question)
    respondent = factories.RespondentFactory(consultation=consultation)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent)

    assert models.ConsultationOld.objects.count() == 1
    assert models.RespondentOld.objects.count() >= 1
    assert models.QuestionOld.objects.count() >= 1
    assert models.QuestionPart.objects.count() >= 1
    assert models.Answer.objects.count() >= 1

    consultation.delete()

    assert models.ConsultationOld.objects.count() == 0
    assert models.RespondentOld.objects.count() == 0
    assert models.QuestionPart.objects.count() == 0
    assert models.Answer.objects.count() == 0
