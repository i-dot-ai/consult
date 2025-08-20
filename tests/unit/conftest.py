import pytest

from consultation_analyser import factories


@pytest.fixture
def question_with_4_responses(free_text_question, respondent_1, respondent_2, respondent_3, respondent_4):
    factories.ResponseFactory(question=free_text_question, respondent=respondent_1)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_2)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_3)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_4)

    yield free_text_question
