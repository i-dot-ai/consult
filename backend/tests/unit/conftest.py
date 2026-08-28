import pytest
from i_dot_ai_utilities.logging._otel import setup as otel_setup

import factories


@pytest.fixture
def otel_enabled(settings):
    settings.OTEL_ENABLED = True


@pytest.fixture
def otel_disabled(settings):
    settings.OTEL_ENABLED = False


@pytest.fixture
def reset_otel():
    otel_setup._reset_for_tests()
    yield
    otel_setup._reset_for_tests()


@pytest.fixture
def question_with_4_responses(free_text_question):
    consultation = free_text_question.consultation
    respondent_1 = factories.RespondentFactory(themefinder_id=1, consultation=consultation)
    respondent_2 = factories.RespondentFactory(themefinder_id=2, consultation=consultation)
    respondent_3 = factories.RespondentFactory(themefinder_id=3, consultation=consultation)
    respondent_4 = factories.RespondentFactory(themefinder_id=4, consultation=consultation)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_1)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_2)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_3)
    factories.ResponseFactory(question=free_text_question, respondent=respondent_4)

    yield free_text_question
