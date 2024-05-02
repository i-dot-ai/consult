from unittest.mock import MagicMock, patch

import boto3

from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker


@check_and_launch_sagemaker
def dummy_function():
    return "Function executed"


def test_check_and_launch_sagemaker_endpoint_exists(settings):
    settings.USE_SAGEMAKER_LLM = True
    with patch("boto3.client") as mock_client:
        # Create a mock SageMaker client
        mock_sagemaker = MagicMock()
        mock_client.return_value = mock_sagemaker
        mock_sagemaker.describe_endpoint.return_value = {
            "EndpointName": "test-endpoint",
        }
        # Try the decorated function
        result = dummy_function()
        assert result == "Function executed"
        mock_sagemaker.create_endpoint.assert_not_called()
        mock_sagemaker.describe_endpoint.assert_called_once_with(EndpointName="test-endpoint")


def test_check_and_launch_sagemaker_endpoint_not_exists(settings):
    settings.USE_SAGEMAKER_LLM = True
    with patch("boto3.client") as mock_client:
        # Create a mock SageMaker client
        mock_sagemaker = MagicMock()
        mock_client.return_value = mock_sagemaker
        mock_sagemaker.describe_endpoint.side_effect = boto3.exceptions.botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "ValidationException", "Message": "Could not find endpoint"}},
            operation_name="describe_endpoint",
        )
        # Try decorated function
        result = dummy_function()
        assert result == "Function executed"
        mock_sagemaker.describe_endpoint.assert_called_once_with(EndpointName="test-endpoint")
        mock_sagemaker.create_endpoint.assert_called_once_with(
            EndpointName="test-endpoint", EndpointConfigName="test-endpoint"
        )


def test_check_and_launch_no_sagemaker():
    # Should run without errors (shouldn't try and access AWS etc)
    result = dummy_function()
    assert result == "Function executed"
