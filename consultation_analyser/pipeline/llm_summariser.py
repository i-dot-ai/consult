import logging

from consultation_analyser.consultations.models import ProcessingRun
from consultation_analyser.pipeline.backends.llm_backend import LLMBackend

logger = logging.getLogger("pipeline")


def create_llm_summaries_for_processing_run(llm_backend: LLMBackend, processing_run: ProcessingRun):
    consultation = processing_run.consultation
    logger.info(
        f"Starting LLM summarisation for consultation: {consultation.name} with backend {llm_backend.__class__.__name__}"
    )

    for theme in processing_run.themes:
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

    logger.info("Save updated theme summaries to data for scatter plot")
    related_topic_model_metadata = processing_run.topic_model_metadatas
    for topic_model_metadata in related_topic_model_metadata:
        topic_model_metadata.add_llm_summarisation_detail()

    logger.info("Ending LLM summarisation")
