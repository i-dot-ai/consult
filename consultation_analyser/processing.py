from django.conf import settings

from consultation_analyser.batch_calls import BatchJobHandler
from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker
from consultation_analyser.consultations.llm_summariser import dummy_generate_theme_summary
from consultation_analyser.consultations.models import Theme
from consultation_analyser.hosting_environment import HostingEnvironment


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


def process_consultation_themes(consultation):
    # Import only when needed
    from consultation_analyser.consultations.ml_pipeline import save_themes_for_consultation

    save_themes_for_consultation(consultation.id)
    create_llm_summaries_for_consultation(consultation)


def run_processing_pipeline(consultation):
    if HostingEnvironment.is_deployed():
        job_name = f"Theme processing pipeline for consultation: {consultation.slug}"
        command = {"command": ["venv/bin/django-admin", "run_ml_pipeline", "--slug", consultation.slug]}
        batch_handler = BatchJobHandler()
        batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
    else:
        process_consultation_themes(consultation)
