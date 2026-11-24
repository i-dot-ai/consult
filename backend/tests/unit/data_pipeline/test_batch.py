from unittest.mock import Mock, patch

import pytest
import structlog
from botocore.exceptions import ClientError

from data_pipeline.batch import submit_job


def configure_settings(settings) -> None:
    settings.SUBMIT_BATCH_JOBS = True
    settings.ASSIGN_THEMES_BATCH_JOB_NAME = "assign-themes-job"
    settings.ASSIGN_THEMES_BATCH_JOB_QUEUE = "assign-themes-queue"
    settings.ASSIGN_THEMES_BATCH_JOB_DEFINITION = "assign-themes-definition"


@patch("data_pipeline.batch.boto3")
@patch("data_pipeline.batch.settings")
def test_submit_assign_themes_job(settings, boto3):
    configure_settings(settings)
    client = Mock()
    client.submit_job.return_value = {"jobId": "job-123"}
    boto3.client.return_value = client
    structlog.contextvars.bind_contextvars(context_id="request-context")
    try:
        result = submit_job(
            job_type="ASSIGN_THEMES",
            consultation_code="consultation",
            consultation_name="Consultation",
            user_id=123,
            model_name="gpt-4.1",
        )
    finally:
        structlog.contextvars.unbind_contextvars("context_id")

    assert result == {"jobId": "job-123"}
    call = client.submit_job.call_args.kwargs
    assert call["jobName"] == "assign-themes-job"
    assert call["parameters"]["context_id"] == "request-context"
    assert call["containerOverrides"]["command"][-1] == "request-context"


@patch("data_pipeline.batch.boto3")
@patch("data_pipeline.batch.settings")
def test_submit_job_is_stubbed_when_batch_is_disabled(settings, boto3):
    settings.SUBMIT_BATCH_JOBS = False

    result = submit_job(
        job_type="ASSIGN_THEMES",
        consultation_code="consultation",
        consultation_name="Consultation",
        user_id=123,
        model_name="gpt-4.1",
    )

    boto3.client.assert_not_called()
    assert result["jobId"] == "local-stub-assign_themes-consultation"


@patch("data_pipeline.batch.logger")
@patch("data_pipeline.batch.boto3")
@patch("data_pipeline.batch.settings")
def test_submit_job_reraises_boto_errors(settings, boto3, logger):
    configure_settings(settings)
    client = Mock()
    client.submit_job.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "AccessDenied"}}, "SubmitJob"
    )
    boto3.client.return_value = client

    with pytest.raises(ClientError):
        submit_job(
            job_type="ASSIGN_THEMES",
            consultation_code="consultation",
            consultation_name="Consultation",
            user_id=123,
            model_name="gpt-4.1",
        )

    logger.exception.assert_called_once()


def test_submit_job_rejects_removed_find_themes_batch_job():
    with pytest.raises(ValueError, match="Unsupported AWS Batch job type: FIND_THEMES"):
        submit_job(
            job_type="FIND_THEMES",  # type: ignore[arg-type]
            consultation_code="consultation",
            consultation_name="Consultation",
            user_id=123,
            model_name="gpt-4.1",
        )
