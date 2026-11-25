from types import SimpleNamespace

import pytest

import factories


@pytest.fixture
def otel_disabled(settings):
    settings.OTEL_CONFIGURED = False


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


@pytest.fixture
def closed_answers(consultation):
    """A hybrid (open question with a closed sibling), a demographic question and an
    untyped legacy question, with three respondents: one multi-select, one single, one silent."""
    closed_question = factories.ClosedQuestionFactory(consultation=consultation, number=11)
    open_question = factories.OpenQuestionFactory(
        consultation=consultation, number=12, closed_question=closed_question
    )
    demographic_question = factories.DemographicQuestionFactory(
        consultation=consultation, number=13
    )
    legacy_question = factories.QuestionFactory(consultation=consultation, number=14)

    multi_select, single, silent = factories.RespondentFactory.create_batch(
        3, consultation=consultation
    )
    for respondent, options in [(multi_select, ["Red", "Blue"]), (single, ["Red"])]:
        for option in options:
            factories.ResponseFactory(
                question=closed_question, respondent=respondent, text=option, free_text=None
            )
    for respondent, region in [(multi_select, "North"), (single, "South"), (silent, "North")]:
        factories.ResponseFactory(
            question=demographic_question, respondent=respondent, text=region, free_text=None
        )
    for respondent in (multi_select, single, silent):
        factories.ResponseFactory(
            question=open_question, respondent=respondent, text="Because", free_text="Because"
        )

    return SimpleNamespace(
        closed_question=closed_question,
        open_question=open_question,
        demographic_question=demographic_question,
        legacy_question=legacy_question,
        multi_select=multi_select,
        single=single,
        silent=silent,
    )
