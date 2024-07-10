import pytest

from consultation_analyser import factories
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.llm_summariser import create_llm_summaries_for_processing_run


@pytest.mark.django_db
def test_create_llm_summaries_for_consultation():
    consultation_builder = factories.ConsultationBuilder()
    theme = consultation_builder.add_theme(summary="", short_description="")
    question = consultation_builder.add_question()
    answer = consultation_builder.add_answer(question)
    answer.themes.add(theme)

    assert not theme.summary
    assert not theme.short_description

    create_llm_summaries_for_processing_run(
        DummyLLMBackend(), consultation_builder.current_processing_run
    )

    theme.refresh_from_db()
    assert theme.summary
    assert theme.short_description
