import datetime
from typing import Literal

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from logging_context import get_context_id

logger = settings.LOGGER


def submit_job(
    job_type: Literal["FIND_THEMES", "ASSIGN_THEMES"],
    consultation_code: str,
    consultation_name: str,
    user_id: int,
    model_name: str,
    assignment_target: Literal["selected_themes", "candidate_themes"] = "selected_themes",
    context_id: str | None = None,
) -> dict | None:
    """
    Submit a job to AWS Batch for ThemeFinder processing.
    This will be either to find themes or assign themes.

    assignment_target controls how the results are imported:
    - "selected_themes": normal flow, imports into ResponseAnnotation
    - "candidate_themes": imports into CandidateThemeResponse (during finalising)

    context_id defaults to the caller's current logging context_id if not supplied,
    so it propagates through to the Batch job's parameters (and from there to the
    EventBridge event and the Lambda that imports the results).
    """
    context_id = context_id or get_context_id()

    if not settings.SUBMIT_BATCH_JOBS:
        logger.info(
            "SUBMIT_BATCH_JOBS disabled: skipping real AWS Batch submission for {job_type}",
            job_type=job_type,
        )
        return {"jobId": f"local-stub-{job_type.lower()}-{consultation_code}"}

    if job_type == "FIND_THEMES":
        job_name = settings.FIND_THEMES_BATCH_JOB_NAME
        job_queue = settings.FIND_THEMES_BATCH_JOB_QUEUE
        job_definition = settings.FIND_THEMES_BATCH_JOB_DEFINITION
    else:
        job_name = settings.ASSIGN_THEMES_BATCH_JOB_NAME
        job_queue = settings.ASSIGN_THEMES_BATCH_JOB_QUEUE
        job_definition = settings.ASSIGN_THEMES_BATCH_JOB_DEFINITION

    parameters = {
        "consultation_code": consultation_code,
        "consultation_name": consultation_name,
        "job_type": job_type,
        "user_id": str(user_id),
        "model_name": model_name,
        "run_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
        "assignment_target": assignment_target,
        "context_id": context_id or "",
    }

    batch = boto3.client("batch")

    logger.info(
        "Submitting {job_type} job to AWS Batch for consultation: {consultation_name}",
        job_type=job_type,
        consultation_name=consultation_name,
    )

    def _log_submit_job_failure(prefix: str) -> None:
        logger.exception(
            prefix + " {job_type} batch job for consultation_code={consultation_code} "
            "(job_queue={job_queue}, job_definition={job_definition})",
            job_type=job_type,
            consultation_code=consultation_code,
            job_queue=job_queue,
            job_definition=job_definition,
        )

    try:
        response = batch.submit_job(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            containerOverrides={
                "command": [
                    "--subdir",
                    consultation_code,
                    "--job-type",
                    job_type,
                    "--model-name",
                    model_name,
                ]
            },
            parameters=parameters,
        )
    except (ClientError, BotoCoreError):
        _log_submit_job_failure("Failed to submit")
        raise
    except Exception:
        _log_submit_job_failure("Unexpected error submitting")
        raise

    job_id = response["jobId"]
    logger.info("Batch job submitted: {job_id}", job_id=job_id)

    return response
