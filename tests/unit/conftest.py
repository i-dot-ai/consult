import pytest

from consultation_analyser import factories


@pytest.fixture
def question_part_with_4_responses():
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    respondent_1 = factories.RespondentFactory(
        themefinder_respondent_id=1, consultation=consultation
    )
    respondent_2 = factories.RespondentFactory(
        themefinder_respondent_id=2, consultation=consultation
    )
    respondent_3 = factories.RespondentFactory(
        themefinder_respondent_id=3, consultation=consultation
    )
    respondent_4 = factories.RespondentFactory(
        themefinder_respondent_id=4, consultation=consultation
    )
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_3)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_4)

    yield question_part
