import django
import pytest

from consultations.models import (
    Question,
    Response,
)
from factories import (
    ClosedQuestionFactory,
    ConsultationFactory,
    DemographicQuestionFactory,
    OpenQuestionFactory,
    QuestionFactory,
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
    assert free_text_question.has_free_text
    assert not free_text_question.has_multiple_choice
    assert free_text_question.answers_question is None

    closed_question = ClosedQuestionFactory()
    assert not closed_question.has_free_text
    assert closed_question.answers_question == closed_question


@pytest.mark.django_db
def test_get_non_empty_responses(consultation, free_text_question):
    respondent1 = RespondentFactory(consultation=consultation)
    respondent2 = RespondentFactory(consultation=consultation)
    respondent3 = RespondentFactory(consultation=consultation)
    ResponseFactory(question=free_text_question, respondent=respondent1, free_text="Has text")
    ResponseFactory(question=free_text_question, respondent=respondent2, free_text="More text")
    ResponseFactory(question=free_text_question, respondent=respondent3, free_text=None)

    result = free_text_question.get_non_empty_responses()

    assert result.count() == 2


@pytest.mark.django_db
class TestSampleResponses:
    def test_keeps_specified_number_of_responses(self):
        consultation = ConsultationFactory()
        question = QuestionFactory(consultation=consultation)
        for i in range(10):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text=f"Response {i}")
        for i in range(5):
            respondent = RespondentFactory(consultation=consultation)
            ResponseFactory(question=question, respondent=respondent, free_text=None)

        result = question.sample_responses(keep_count=3)

        assert result.kept == 3
        assert result.deleted == 12
        assert Response.objects.filter(question=question).count() == 3

        question.refresh_from_db()

        assert question.free_text_response_count == 3

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


@pytest.mark.django_db
def test_answers_question_is_self_for_chartable_questions():
    closed_question = ClosedQuestionFactory()
    demographic_question = DemographicQuestionFactory()
    assert closed_question.answers_question == closed_question
    assert demographic_question.answers_question == demographic_question


@pytest.mark.django_db
def test_answers_question_is_the_closed_sibling_for_a_hybrid():
    closed_question = ClosedQuestionFactory()
    open_question = OpenQuestionFactory(
        consultation=closed_question.consultation, closed_question=closed_question
    )
    assert open_question.answers_question == closed_question


@pytest.mark.django_db
def test_answers_question_is_none_without_answers_to_read():
    assert OpenQuestionFactory().answers_question is None
    assert QuestionFactory().answers_question is None


@pytest.mark.django_db
def test_answers_question_id_reads_no_related_question(django_assert_num_queries):
    closed_question = ClosedQuestionFactory()
    open_question = OpenQuestionFactory(
        consultation=closed_question.consultation, closed_question=closed_question
    )
    open_question = Question.objects.get(id=open_question.id)
    with django_assert_num_queries(0):
        assert open_question.answers_question_id == closed_question.id


@pytest.mark.django_db
def test_calculate_response_counts_counts_answering_respondents_for_a_hybrid(closed_answers):
    open_question = closed_answers.open_question
    open_question.has_multiple_choice = True

    open_question.calculate_response_counts()
    assert open_question.multi_choice_response_count == 2

    single_only = open_question.response_set.filter(respondent=closed_answers.single)
    open_question.calculate_response_counts(single_only)
    assert open_question.multi_choice_response_count == 1


@pytest.mark.django_db
def test_calculate_response_counts_is_zero_for_an_open_question_without_a_sibling(
    closed_answers,
):
    question = OpenQuestionFactory(consultation=closed_answers.open_question.consultation)
    question.has_multiple_choice = True
    question.calculate_response_counts()
    assert question.multi_choice_response_count == 0


@pytest.mark.django_db
def test_unfiltered_counts_include_respondents_who_only_answered_the_closed_part(
    closed_answers,
):
    closed_only = RespondentFactory(consultation=closed_answers.open_question.consultation)
    ResponseFactory(
        question=closed_answers.closed_question, respondent=closed_only, text="Blue", free_text=None
    )

    closed_answers.open_question.calculate_response_counts()
    assert closed_answers.open_question.multi_choice_response_count == 3
    assert closed_answers.open_question.total_response_count == 4

    closed_answers.open_question.calculate_response_counts(
        closed_answers.open_question.response_set.all()
    )
    assert closed_answers.open_question.multi_choice_response_count == 2
