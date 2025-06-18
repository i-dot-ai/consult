import pytest

from consultation_analyser import factories


@pytest.fixture
def question_with_4_responses():
    question = factories.QuestionFactory()
    consultation = question.consultation
    respondent_1 = factories.RespondentFactory(themefinder_id=1, consultation=consultation)
    respondent_2 = factories.RespondentFactory(themefinder_id=2, consultation=consultation)
    respondent_3 = factories.RespondentFactory(themefinder_id=3, consultation=consultation)
    respondent_4 = factories.RespondentFactory(themefinder_id=4, consultation=consultation)
    factories.ResponseFactory(question=question, respondent=respondent_1)
    factories.ResponseFactory(question=question, respondent=respondent_2)
    factories.ResponseFactory(question=question, respondent=respondent_3)
    factories.ResponseFactory(question=question, respondent=respondent_4)

    yield question
