import django
import pytest
from backend.consultations.models import (
    Question,
    Response,
)
from backend.factories import (
    ConsultationFactory,
    QuestionFactory,
    QuestionWithBothFactory,
    QuestionWithMultipleChoiceFactory,
    RespondentFactory,
    ResponseFactory,
)


@pytest.mark.django_db
def test_initial_question_theme_status():
    question = Question()
    assert question.theme_status == Question.ThemeStatus.DRAFT


@pytest.mark.django_db
def test_unique_question_number():
    question_1 = QuestionFactory(number=1, text="question text")
    consultation = question_1.consultation
    question_2 = QuestionFactory(consultation=consultation, number=2)
    assert question_1.number != question_2.number
    with pytest.raises(django.db.utils.IntegrityError):
        Question.objects.get_or_create(consultation=consultation, number=1, text="different text")


@pytest.mark.django_db
def test_question_configuration(free_text_question):
    # Test free text only question (default)
    assert free_text_question.has_free_text
    assert not free_text_question.has_multiple_choice
    assert free_text_question.multiple_choice_options == []

    # Test multiple choice only question
    mc_question = QuestionWithMultipleChoiceFactory()
    assert mc_question.has_multiple_choice
    assert not mc_question.has_free_text  # Factory sets this to False
    assert isinstance(mc_question.multiple_choice_options, list)
    assert len(mc_question.multiple_choice_options) >= 2

    # Test question with both
    both_question = QuestionWithBothFactory()
    assert both_question.has_free_text
    assert both_question.has_multiple_choice
    assert isinstance(both_question.multiple_choice_options, list)


@pytest.mark.django_db
def test_get_non_empty_responses(consultation, free_text_question):
    respondent1 = RespondentFactory(consultation=consultation)
    respondent2 = RespondentFactory(consultation=consultation)
    respondent3 = RespondentFactory(consultation=consultation)
    respondent4 = RespondentFactory(consultation=consultation)
    ResponseFactory(question=free_text_question, respondent=respondent1, free_text="Has text")
    ResponseFactory(question=free_text_question, respondent=respondent2, free_text="Not Provided")
    ResponseFactory(question=free_text_question, respondent=respondent3, free_text="")
    ResponseFactory(question=free_text_question, respondent=respondent4, free_text=None)

    result = free_text_question.get_non_empty_responses()

    assert result.count() == 1


@pytest.mark.django_db
class TestSampleResponses:
    def test_keeps_specified_number_of_responses(self):
        consultation = ConsultationFactory()
        question = QuestionFactory(consultation=consultation)
        for i in range(5):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text=f"Response {i}")
        for i in range(5):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text="Not Provided")
        for i in range(5):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text="")
        for i in range(5):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text=None)

        result = question.sample_responses(keep_count=3)

        assert result.kept == 3
        assert result.deleted == 17
        assert Response.objects.filter(question=question).count() == 3

        question.refresh_from_db()

        assert question.total_responses == 3

    def test_raises_error_if_keep_count_less_than_one(self):
        consultation = ConsultationFactory()
        question = QuestionFactory(consultation=consultation)
        respondent = RespondentFactory(consultation=consultation)
        ResponseFactory(question=question, respondent=respondent, free_text="Response")

        with pytest.raises(ValueError) as exc_info:
            question.sample_responses(keep_count=0)

        assert str(exc_info.value) == "Number of responses to keep must be at least 1"

    def test_raises_error_if_keep_count_exceeds_count(self):
        consultation = ConsultationFactory()
        question = QuestionFactory(consultation=consultation)
        respondent = RespondentFactory(consultation=consultation)
        ResponseFactory(question=question, respondent=respondent, free_text="Response")

        with pytest.raises(ValueError) as exc_info:
            question.sample_responses(keep_count=5)

        assert (
            str(exc_info.value)
            == "Number of responses to keep (5) cannot exceed current number of responses (1)"
        )
