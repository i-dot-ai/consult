import pytest
from django.core.exceptions import ValidationError

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.parametrize(
    "input_keywords,topic_id,is_outlier",
    [(["key", "lock"], 2, False), (["dog", "cat"], -1, True)],
)
@pytest.mark.django_db
def test_save_theme_to_answer(input_keywords, topic_id, is_outlier):
    consultation = factories.ConsultationWithAnswersFactory()
    answer = models.Answer.objects.last()
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    tmm = factories.TopicModelMetadataFactory()

    #  Check theme created and saved to answer
    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=tmm,
    )
    theme = models.Theme.objects.get(topic_keywords=input_keywords)
    assert theme.topic_keywords == input_keywords
    assert theme.is_outlier == is_outlier

    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=tmm,
    )

    themes_qs = models.Theme.objects.filter(topic_keywords=input_keywords)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_multiple_choice_validation():
    question = factories.QuestionFactory()
    resp = factories.ConsultationResponseFactory(consultation=question.section.consultation)
    a = factories.AnswerFactory(question=question, consultation_response=resp)

    a.multiple_choice = {"totally": "invalid"}

    with pytest.raises(ValidationError):
        a.full_clean()


@pytest.mark.django_db
def test_find_answer_multiple_choice_response():
    q = factories.QuestionFactory(
        multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])]
    )
    resp = factories.ConsultationResponseFactory(consultation=q.section.consultation)

    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["Yes"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )

    result = models.Answer.objects.filter_multiple_choice(question="Not a question", answer="Yes")
    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="wrong")
    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="Yes")
    assert result.count() == 1

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="No")
    assert result.count() == 2
