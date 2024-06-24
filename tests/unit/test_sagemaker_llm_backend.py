from unittest.mock import patch

from consultation_analyser.pipeline.backends.sagemaker_llm_backend import SagemakerLLMBackend
from tests.helpers import mock_sagemaker


def test_sagemaker_describe_is_called():
    with mock_sagemaker() as sagemaker:
        backend = SagemakerLLMBackend()

        backend.llm.invoke("hello there")

        sagemaker.create_endpoint.assert_not_called()
        sagemaker.describe_endpoint.assert_called()


@patch("time.sleep", return_value=None)  # don't wait to retry on sagemaker
def test_sagemaker_create_is_called(_sleep):
    with mock_sagemaker(available=False) as sagemaker:
        backend = SagemakerLLMBackend()

        backend.llm.invoke("hello there")

        sagemaker.describe_endpoint.assert_called_with(EndpointName="test-endpoint")
        sagemaker.create_endpoint.assert_called_once_with(
            EndpointName="test-endpoint", EndpointConfigName="test-endpoint"
        )
