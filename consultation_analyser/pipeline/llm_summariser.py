import logging

from consultation_analyser.consultations.models import Theme
from consultation_analyser.pipeline.backends.llm_backend import LLMBackend

logger = logging.getLogger("pipeline")


def create_llm_summaries_for_consultation(consultation, llm_backend: LLMBackend):
    logger.info(
        f"Starting LLM summarisation for consultation: {consultation.name} with backend {llm_backend.__class__.__name__}"
    )
    themes = Theme.objects.filter(
        topic_model_metadata__processing_run__consultation=consultation
    ).filter(topic_model_metadata__question__has_free_text=True)

    for theme in themes:
        logger.info(f"Starting LLM summarisation for theme with keywords: {theme.topic_keywords}")
        theme_summary_data = llm_backend.summarise_theme(theme)
        theme.summary = theme_summary_data.summary
        theme.short_description = theme_summary_data.short_description
        logger.info(f"Theme description: {theme.short_description}")
        theme.save()
