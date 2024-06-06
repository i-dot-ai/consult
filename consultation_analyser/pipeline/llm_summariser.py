import logging

from consultation_analyser.consultations.models import Theme
from consultation_analyser.pipeline.backends.llm_backend import LLMBackend

from .backends.types import ThemeSummary

logger = logging.getLogger("django.server")


def create_llm_summaries_for_consultation(consultation, llm_backend: LLMBackend):
    logger.info(
        f"Starting LLM summarisation for consultation: {consultation.name} with backend {llm_backend.__class__.__name__}"
    )
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(
        question__has_free_text=True
    )

    theme: ThemeSummary
    for theme in themes:
        theme_summary_data = llm_backend.summarise_theme(theme)
        theme.summary = theme_summary_data.summary
        theme.short_description = theme_summary_data.short_description
        logger.info(f"Theme description: {theme.short_description}")
        theme.save()
