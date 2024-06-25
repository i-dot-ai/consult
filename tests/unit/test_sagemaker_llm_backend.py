from unittest.mock import patch

import pytest

from consultation_analyser.pipeline.backends.sagemaker_llm_backend import (
    SagemakerFailureException,
    SagemakerLLMBackend,
)
from tests.helpers import mock_sagemaker


def test_sagemaker_describe_is_called():
    with mock_sagemaker() as sagemaker:
        backend = SagemakerLLMBackend()

        backend.llm.invoke("hello there")

        sagemaker.create_endpoint.assert_not_called()
        sagemaker.describe_endpoint.assert_called()


@patch("time.sleep", return_value=None)  # don't wait to retry on sagemaker
def test_sagemaker_create_is_called(_sleep):
    with mock_sagemaker(state="inactive") as sagemaker:
        backend = SagemakerLLMBackend()

        backend.llm.invoke("hello there")

        sagemaker.describe_endpoint.assert_called_with(EndpointName="test-endpoint")
        sagemaker.create_endpoint.assert_called_once_with(
            EndpointName="test-endpoint", EndpointConfigName="test-endpoint"
        )


@patch("time.sleep", return_value=None)  # don't wait to retry on sagemaker
def test_sagemaker_throws_when_failed(_sleep):
    with mock_sagemaker(state="failed"):
        backend = SagemakerLLMBackend()

        with pytest.raises(SagemakerFailureException):
            backend.llm.invoke("hello there")
