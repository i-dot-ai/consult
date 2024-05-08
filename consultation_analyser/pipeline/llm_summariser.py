"""
Use LLMs to generate summaries for themes. More to follow!
"""
from django.conf import settings

from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker
from consultation_analyser.consultations.models import Theme


def dummy_generate_theme_summary(theme: Theme) -> dict[str, str]:
    made_up_short_description = (", ").join(theme.keywords)
    made_up_summary = f"Longer summary: {made_up_short_description}"
    output = {"phrase": made_up_short_description, "summary": made_up_summary}
    return output


@check_and_launch_sagemaker
def create_llm_summaries_for_consultation(consultation):
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(question__has_free_text=True)
    for theme in themes:
        if settings.USE_SAGEMAKER_LLM:
            # TODO - to be replaced by a real version!
            theme_summary_data = dummy_generate_theme_summary(theme)
        else:
            theme_summary_data = dummy_generate_theme_summary(theme)
        theme.summary = theme_summary_data["summary"]
        theme.short_description = theme_summary_data["phrase"]
        theme.save()
