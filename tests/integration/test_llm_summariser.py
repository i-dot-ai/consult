import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import Theme
from consultation_analyser.pipeline.llm_summariser import create_llm_summaries_for_consultation


@pytest.mark.django_db
def test_create_llm_summaries_for_consultation():
    consultation = factories.ConsultationFactory(name="My new consultation")
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section, has_free_text=True)
    theme = factories.ThemeFactory(question=question, short_description="", summary="")
    theme_id = theme.id
    # Check that we create some value for theme summary and description
    assert not theme.summary
    assert not theme.short_description
    create_llm_summaries_for_consultation(consultation)
    theme = Theme.objects.get(id=theme_id)
    assert theme.summary
    assert theme.short_description
