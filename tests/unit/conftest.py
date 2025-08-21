import pytest

from consultation_analyser import factories


@pytest.fixture
def question_with_4_responses(free_text_question, response_1, response_2, response_3, response_4):

    yield free_text_question
