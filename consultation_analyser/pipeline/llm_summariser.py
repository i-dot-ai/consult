import logging

from consultation_analyser.consultations.models import Answer, Question, Theme
from consultation_analyser.pipeline.backends.llm_backend import LLMBackend

logger = logging.getLogger("pipeline")


def create_llm_summaries_for_consultation(consultation, llm_backend: LLMBackend):
    logger.info(
        f"Starting LLM summarisation for consultation: {consultation.name} with backend {llm_backend.__class__.__name__}"
    )
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(
        question__has_free_text=True
    )

    for theme in themes:
        logger.info(f"Starting LLM summarisation for theme with keywords: {theme.topic_keywords}")
        if theme.is_outlier:
            theme.short_description = "Outliers"
            theme.summary = "These are responses that don't fit into the identified themes."
            logger.info(f"Saving an outlier theme for question: {theme.question.text}")
        else:
            theme_summary_data = llm_backend.summarise_theme(theme)
            theme.summary = theme_summary_data.summary
            theme.short_description = theme_summary_data.short_description
            logger.info(f"Theme description: {theme.short_description}")
        theme.save()

    # If there are answers with empty free text - create a special case theme to group them
    free_text_questions = Question.objects.filter(section__consultation=consultation).filter(
        has_free_text=True
    )
    for question in free_text_questions:
        empty_answers = Answer.objects.filter(question=question).filter(free_text="")
        for answer in empty_answers:
            theme, _ = Theme.objects.get_or_create(
                question=question, topic_id=None, short_description="No free text response", summary="The respondent did not answer the free text part of this question."
            )
            logger.info(
                f"There are answers with no free text responses for question: {theme.question.text}"
            )
            answer.theme = theme
            answer.save()
    logger.info("Ending LLM summarisation")
