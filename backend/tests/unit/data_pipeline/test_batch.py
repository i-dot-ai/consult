from unittest.mock import Mock, patch

import pytest
import structlog
from botocore.exceptions import ClientError

from data_pipeline.batch import submit_job


class TestSubmitBatchJob:
    @staticmethod
    def _configure_batch_job_settings(mock_settings, job_type: str) -> None:
        mock_settings.SUBMIT_BATCH_JOBS = True
        setattr(mock_settings, f"{job_type}_BATCH_JOB_NAME", f"{job_type.lower()}-job".replace("_", "-"))
        setattr(mock_settings, f"{job_type}_BATCH_JOB_QUEUE", f"{job_type.lower()}-queue".replace("_", "-"))
        setattr(mock_settings, f"{job_type}_BATCH_JOB_DEFINITION", f"{job_type.lower()}-def".replace("_", "-"))

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_find_themes_job(self, mock_settings, mock_boto3):
        """Test submitting a FIND_THEMES batch job"""
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        # Mock boto3 batch client
        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id-123"}
        mock_boto3.client.return_value = mock_batch_client

        # Submit job
        structlog.contextvars.bind_contextvars(context_id="request-context-id")
        try:
            response = submit_job(
                job_type="FIND_THEMES",
                consultation_code="test-code",
                consultation_name="Test Consultation",
                user_id=123,
                model_name="my-model",
            )
        finally:
            structlog.contextvars.unbind_contextvars("context_id")

        # Verify batch client was called correctly
        mock_boto3.client.assert_called_once_with("batch")
        mock_batch_client.submit_job.assert_called_once()

        call_args = mock_batch_client.submit_job.call_args.kwargs
        assert call_args["jobName"] == "find-themes-job"
        assert call_args["jobQueue"] == "find-themes-queue"
        assert call_args["jobDefinition"] == "find-themes-def"
        assert call_args["containerOverrides"]["command"] == [
            "--subdir",
            "test-code",
            "--job-type",
            "FIND_THEMES",
            "--model-name",
            "my-model",
            "--context-id",
            "request-context-id",
        ]
        assert call_args["parameters"]["consultation_code"] == "test-code"
        assert call_args["parameters"]["consultation_name"] == "Test Consultation"
        assert call_args["parameters"]["job_type"] == "FIND_THEMES"
        assert call_args["parameters"]["user_id"] == "123"
        assert "run_date" in call_args["parameters"]

        # Verify response
        assert response["jobId"] == "test-job-id-123"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_assign_themes_job(self, mock_settings, mock_boto3):
        """Test submitting an ASSIGN_THEMES batch job"""
        self._configure_batch_job_settings(mock_settings, "ASSIGN_THEMES")

        # Mock boto3 batch client
        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id-456"}
        mock_boto3.client.return_value = mock_batch_client

        # Submit job
        response = submit_job(
            job_type="ASSIGN_THEMES",
            consultation_code="test-code-2",
            consultation_name="Test Consultation 2",
            user_id=456,
            model_name="my-model",
        )

        # Verify batch client was called correctly
        call_args = mock_batch_client.submit_job.call_args.kwargs
        assert call_args["jobName"] == "assign-themes-job"
        assert call_args["jobQueue"] == "assign-themes-queue"
        assert call_args["jobDefinition"] == "assign-themes-def"
        assert call_args["containerOverrides"]["command"] == [
            "--subdir",
            "test-code-2",
            "--job-type",
            "ASSIGN_THEMES",
            "--model-name",
            "my-model",
        ]
        assert call_args["parameters"]["job_type"] == "ASSIGN_THEMES"

        # Verify response
        assert response["jobId"] == "test-job-id-456"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_propagates_context_id(self, mock_settings, mock_boto3):
        """The caller's context_id is appended as --context-id so pipeline logs can be joined"""
        mock_settings.SUBMIT_BATCH_JOBS = True
        mock_settings.FIND_THEMES_BATCH_JOB_NAME = "find-themes-job"
        mock_settings.FIND_THEMES_BATCH_JOB_QUEUE = "find-themes-queue"
        mock_settings.FIND_THEMES_BATCH_JOB_DEFINITION = "find-themes-def"

        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id-789"}
        mock_boto3.client.return_value = mock_batch_client

        structlog.contextvars.bind_contextvars(context_id="request-context-abc")
        try:
            submit_job(
                job_type="FIND_THEMES",
                consultation_code="test-code",
                consultation_name="Test Consultation",
                user_id=123,
                model_name="my-model",
            )
        finally:
            structlog.contextvars.unbind_contextvars("context_id")

        command = mock_batch_client.submit_job.call_args.kwargs["containerOverrides"]["command"]
        assert "--context-id" in command
        assert command[command.index("--context-id") + 1] == "request-context-abc"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_omits_context_id_when_absent(self, mock_settings, mock_boto3):
        """When no context_id is bound, --context-id is omitted from the command"""
        mock_settings.SUBMIT_BATCH_JOBS = True
        mock_settings.FIND_THEMES_BATCH_JOB_NAME = "find-themes-job"
        mock_settings.FIND_THEMES_BATCH_JOB_QUEUE = "find-themes-queue"
        mock_settings.FIND_THEMES_BATCH_JOB_DEFINITION = "find-themes-def"

        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id"}
        mock_boto3.client.return_value = mock_batch_client

        submit_job(
            job_type="FIND_THEMES",
            consultation_code="test-code",
            consultation_name="Test Consultation",
            user_id=123,
            model_name="my-model",
        )

        command = mock_batch_client.submit_job.call_args.kwargs["containerOverrides"]["command"]
        assert "--context-id" not in command

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_stubbed_when_batch_disabled(self, mock_settings, mock_boto3):
        """When SUBMIT_BATCH_JOBS is disabled, return a stub and never call AWS Batch"""
        mock_settings.SUBMIT_BATCH_JOBS = False

        response = submit_job(
            job_type="ASSIGN_THEMES",
            consultation_code="test-code-3",
            consultation_name="Test Consultation 3",
            user_id=789,
            model_name="my-model",
        )

        # No real AWS Batch client is created or called
        mock_boto3.client.assert_not_called()

        # A stub response with a jobId is returned so callers keep working
        assert "jobId" in response
        assert "test-code-3" in response["jobId"]

    @patch("data_pipeline.batch.logger")
    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_reraises_boto_errors(self, mock_settings, mock_boto3, mock_logger):
        """Boto-specific errors are logged via the ClientError/BotoCoreError branch and re-raised unchanged"""
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        mock_batch_client = Mock()
        mock_batch_client.submit_job.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "AccessDenied"}}, "SubmitJob"
        )
        mock_boto3.client.return_value = mock_batch_client

        with pytest.raises(ClientError):
            submit_job(
                job_type="FIND_THEMES",
                consultation_code="test-code",
                consultation_name="Test Consultation",
                user_id=123,
                model_name="my-model",
            )

        mock_logger.exception.assert_called_once()
        message, kwargs = mock_logger.exception.call_args[0][0], mock_logger.exception.call_args[1]
        assert "Failed to submit" in message
        assert kwargs["job_type"] == "FIND_THEMES"
        assert kwargs["consultation_code"] == "test-code"

    @patch("data_pipeline.batch.logger")
    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_reraises_unexpected_errors(self, mock_settings, mock_boto3, mock_logger):
        """Non-boto errors hit the separate catch-all branch, are logged, and re-raised, not swallowed"""
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        mock_batch_client = Mock()
        mock_batch_client.submit_job.side_effect = ValueError("unexpected failure")
        mock_boto3.client.return_value = mock_batch_client

        with pytest.raises(ValueError, match="unexpected failure"):
            submit_job(
                job_type="FIND_THEMES",
                consultation_code="test-code",
                consultation_name="Test Consultation",
                user_id=123,
                model_name="my-model",
            )

        mock_logger.exception.assert_called_once()
        message, kwargs = mock_logger.exception.call_args[0][0], mock_logger.exception.call_args[1]
        assert "Unexpected error submitting" in message
        assert kwargs["job_type"] == "FIND_THEMES"
        assert kwargs["consultation_code"] == "test-code"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_defaults_context_id_from_ambient(self, mock_settings, mock_boto3):
        """When no context_id is passed explicitly, submit_job picks up whatever's
        currently bound to the logger, so the caller's action id propagates through
        to the Batch job's parameters (and from there to the Lambda that imports
        the results)."""
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id"}
        mock_boto3.client.return_value = mock_batch_client

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(context_id="ambient-id")

        submit_job(
            job_type="FIND_THEMES",
            consultation_code="test-code",
            consultation_name="Test Consultation",
            user_id=123,
            model_name="my-model",
        )

        call_args = mock_batch_client.submit_job.call_args.kwargs
        assert call_args["parameters"]["context_id"] == "ambient-id"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_explicit_context_id_overrides_ambient(self, mock_settings, mock_boto3):
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id"}
        mock_boto3.client.return_value = mock_batch_client

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(context_id="ambient-id")

        submit_job(
            job_type="FIND_THEMES",
            consultation_code="test-code",
            consultation_name="Test Consultation",
            user_id=123,
            model_name="my-model",
            context_id="explicit-id",
        )

        call_args = mock_batch_client.submit_job.call_args.kwargs
        assert call_args["parameters"]["context_id"] == "explicit-id"

    @patch("data_pipeline.batch.boto3")
    @patch("data_pipeline.batch.settings")
    def test_submit_job_with_no_context_sends_empty_string(self, mock_settings, mock_boto3):
        """AWS Batch parameters must be strings, so an unset context_id becomes ""
        rather than None."""
        self._configure_batch_job_settings(mock_settings, "FIND_THEMES")

        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id"}
        mock_boto3.client.return_value = mock_batch_client

        structlog.contextvars.clear_contextvars()

        submit_job(
            job_type="FIND_THEMES",
            consultation_code="test-code",
            consultation_name="Test Consultation",
            user_id=123,
            model_name="my-model",
        )

        call_args = mock_batch_client.submit_job.call_args.kwargs
        assert call_args["parameters"]["context_id"] == ""
