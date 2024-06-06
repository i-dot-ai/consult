from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.backends.bertopic import BERTopicBackend
from consultation_analyser.pipeline.batch_calls import BatchJobHandler
from consultation_analyser.pipeline.llm_summariser import (
    create_llm_summaries_for_consultation,
)
from consultation_analyser.pipeline.ml_pipeline import save_themes_for_consultation


def process_consultation_themes(consultation, topic_backend=None, llm=None):
    if not topic_backend:
        topic_backend = BERTopicBackend()

    save_themes_for_consultation(consultation.id, topic_backend)

    if llm:
        create_llm_summaries_for_consultation(consultation, llm)
    else:
        create_llm_summaries_for_consultation(consultation)


def run_processing_pipeline(consultation):
    if HostingEnvironment.is_deployed():
        job_name = f"generate-themes-{consultation.slug}"[:128]  # Must be <=128 , no spaces
        command = {
            "command": [
                "venv/bin/django-admin",
                "run_ml_pipeline",
                "--consultation_slug",
                consultation.slug,
            ]
        }
        batch_handler = BatchJobHandler()
        batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
    else:
        process_consultation_themes(consultation)
