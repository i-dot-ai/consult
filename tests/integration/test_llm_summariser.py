import pytest

from consultation_analyser import factories
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.llm_summariser import create_llm_summaries_for_consultation


@pytest.mark.django_db
def test_create_llm_summaries_for_consultation():
    consultation = factories.ConsultationFactory(name="My new consultation")
    response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section, has_free_text=True)
    theme = factories.ThemeFactory(question=question, short_description="", summary="")
    factories.AnswerFactory(theme=theme, question=question, consultation_response=response)

    assert not theme.summary
    assert not theme.short_description

    create_llm_summaries_for_consultation(consultation, DummyLLMBackend())

    theme.refresh_from_db()
    assert theme.summary
    assert theme.short_description
