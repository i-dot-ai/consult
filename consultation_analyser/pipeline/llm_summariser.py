"""
Use LLMs to generate summaries for themes. More to follow!
"""
from django.conf import settings

from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker
from consultation_analyser.consultations.models import Theme


def dummy_generate_theme_summary(theme: Theme) -> str:
    made_up_summary = (", ").join(theme.keywords)
    return made_up_summary


@check_and_launch_sagemaker
def create_llm_summaries_for_consultation(consultation):
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(question__has_free_text=True)
    for theme in themes:
        if settings.USE_SAGEMAKER_LLM:
            # TODO - to be replaced by a real version!
            summary = dummy_generate_theme_summary(theme)
        else:
            summary = dummy_generate_theme_summary(theme)
        theme.summary = summary
        theme.save()
