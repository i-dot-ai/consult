from consultation_analyser.consultation.models import Theme
from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker
from consultation_analyser.consultations.llm_summariser import dummy_generate_theme_summary
from consultation_analyser.consultations.ml_pipeline import save_themes_for_consultation


@check_and_launch_sagemaker
def create_llm_summaries_for_consultation(consultation):
    themes = Theme.objects.filter(question__consultation=consultation).filter(question__has_free_text=True)
    for theme in themes:
        summary = dummy_generate_theme_summary(theme)
        theme.summary = summary
        theme.save()


def process_consultation_themes(consultation):
    save_themes_for_consultation(consultation.id)
    create_llm_summaries_for_consultation(consultation)
