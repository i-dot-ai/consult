import datetime
from typing import Literal

import boto3
from django.conf import settings

logger = settings.LOGGER


def submit_job(
    job_type: Literal["FIND_THEMES", "ASSIGN_THEMES"],
    consultation_code: str,
    consultation_name: str,
    user_id: int,
) -> dict:
    """
    Submit a job to AWS Batch for ThemeFinder processing.
    This will be either to find themes or assign themes.
    """
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
        "run_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
    }

    batch = boto3.client("batch")

    logger.info(f"Submitting {job_type} job to AWS Batch for consultation: {consultation_name}")

    response = batch.submit_job(
        jobName=job_name,
        jobQueue=job_queue,
        jobDefinition=job_definition,
        containerOverrides={"command": ["--subdir", consultation_code, "--job-type", job_type]},
        parameters=parameters,
    )

    job_id = response["jobId"]
    logger.info(f"Batch job submitted: {job_id}")

    return response
