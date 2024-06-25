import logging

from consultation_analyser.consultations.models import ProcessingRun, Theme
from consultation_analyser.pipeline.backends.llm_backend import LLMBackend

<<<<<<< HEAD
=======

>>>>>>> cf501de (format code)
logger = logging.getLogger("pipeline")


def create_llm_summaries_for_consultation(
    consultation, llm_backend: LLMBackend, processing_run: ProcessingRun
):
    logger.info(
        f"Starting LLM summarisation for consultation: {consultation.name} with backend {llm_backend.__class__.__name__}"
    )
    themes = Theme.objects.filter(topic_model__processing_run=processing_run)

    for theme in themes:
        logger.info(f"Starting LLM summarisation for theme with keywords: {theme.topic_keywords}")
        if theme.is_outlier:
            theme.short_description = "Outliers"
            theme.summary = "These are responses that don't fit into the identified themes."
        else:
            theme_summary_data = llm_backend.summarise_theme(theme)
            theme.summary = theme_summary_data.summary
            theme.short_description = theme_summary_data.short_description
        logger.info(f"Theme description: {theme.short_description}")
        theme.save()
    logger.info("Ending LLM summarisation")
