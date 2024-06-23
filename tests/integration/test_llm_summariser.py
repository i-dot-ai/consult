import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import Theme
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.llm_summariser import create_llm_summaries_for_consultation


@pytest.mark.django_db
def test_create_llm_summaries_for_consultation():
    consultation = factories.ConsultationFactory(name="My new consultation")
    response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section, has_free_text=True)
    outlier_theme = factories.ThemeFactory(
        question=question, topic_id=-1, short_description="", summary=""
    )
    normal_theme = factories.ThemeFactory(
        question=question, topic_id=2, short_description="", summary=""
    )
    factories.AnswerFactory(
        theme=outlier_theme,
        free_text="this is an outlier",
        question=question,
        consultation_response=response,
    )
    factories.AnswerFactory(
        theme=normal_theme,
        free_text="this is a normal response",
        question=question,
        consultation_response=response,
    )
    factories.AnswerFactory(
        theme=None, free_text="", question=question, consultation_response=response
    )

    assert not outlier_theme.summary
    assert not outlier_theme.short_description

    create_llm_summaries_for_consultation(consultation, DummyLLMBackend())

    outlier_theme.refresh_from_db()
    assert not outlier_theme.summary
    assert outlier_theme.short_description == "Outliers"

    normal_theme.refresh_from_db()
    assert normal_theme.summary
    assert normal_theme.short_description

    no_responses_theme = Theme.objects.get(topic_id=None)
    no_responses_theme.short_description == "No free text response"
