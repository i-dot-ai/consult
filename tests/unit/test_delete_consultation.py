import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_delete_consultation():
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(consultation=consultation)
    question_part = factories.FreeTextQuestionPartFactory(question=question)
    respondent = factories.RespondentFactory(consultation=consultation)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent)

    assert models.Consultation.objects.count() == 1
    assert models.Respondent.objects.count() >= 1
    assert models.Question.objects.count() >= 1
    assert models.QuestionPart.objects.count() >= 1
    assert models.Answer.objects.count() >= 1

    consultation.delete()

    assert models.Consultation.objects.count() == 0
    assert models.Respondent.objects.count() == 0
    assert models.QuestionPart.objects.count() == 0
    assert models.Answer.objects.count() == 0
