from unittest.mock import Mock, patch

from backend.data_pipeline.batch import submit_job


class TestSubmitBatchJob:
    @patch("backend.data_pipeline.batch.boto3")
    @patch("backend.data_pipeline.batch.settings")
    def test_submit_find_themes_job(self, mock_settings, mock_boto3):
        """Test submitting a FIND_THEMES batch job"""
        # Mock settings
        mock_settings.FIND_THEMES_BATCH_JOB_NAME = "find-themes-job"
        mock_settings.FIND_THEMES_BATCH_JOB_QUEUE = "find-themes-queue"
        mock_settings.FIND_THEMES_BATCH_JOB_DEFINITION = "find-themes-def"

        # Mock boto3 batch client
        mock_batch_client = Mock()
        mock_batch_client.submit_job.return_value = {"jobId": "test-job-id-123"}
        mock_boto3.client.return_value = mock_batch_client

        # Submit job
        response = submit_job(
            job_type="FIND_THEMES",
            consultation_code="test-code",
            consultation_name="Test Consultation",
            user_id=123,
        )

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
        ]
        assert call_args["parameters"]["consultation_code"] == "test-code"
        assert call_args["parameters"]["consultation_name"] == "Test Consultation"
        assert call_args["parameters"]["job_type"] == "FIND_THEMES"
        assert call_args["parameters"]["user_id"] == "123"
        assert "run_date" in call_args["parameters"]

        # Verify response
        assert response["jobId"] == "test-job-id-123"

    @patch("backend.data_pipeline.batch.boto3")
    @patch("backend.data_pipeline.batch.settings")
    def test_submit_assign_themes_job(self, mock_settings, mock_boto3):
        """Test submitting an ASSIGN_THEMES batch job"""
        # Mock settings
        mock_settings.ASSIGN_THEMES_BATCH_JOB_NAME = "assign-themes-job"
        mock_settings.ASSIGN_THEMES_BATCH_JOB_QUEUE = "assign-themes-queue"
        mock_settings.ASSIGN_THEMES_BATCH_JOB_DEFINITION = "assign-themes-def"

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
        ]
        assert call_args["parameters"]["job_type"] == "ASSIGN_THEMES"

        # Verify response
        assert response["jobId"] == "test-job-id-456"
