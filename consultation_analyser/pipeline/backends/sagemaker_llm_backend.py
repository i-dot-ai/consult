import json

import boto3
from django.conf import settings
from langchain_community.llms import SagemakerEndpoint
from langchain_community.llms.sagemaker_endpoint import LLMContentHandler

from consultation_analyser.pipeline.decorators import check_and_launch_sagemaker

from .langchain_llm_backend import LangchainLLMBackend


class SagemakerContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, inputs: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"inputs": inputs, "parameters": model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


class SagemakerLLMBackend(LangchainLLMBackend):
    def __init__(self):
        super().__init__(self.__get_sagemaker_endpoint())

    @check_and_launch_sagemaker
    def __get_sagemaker_endpoint(self) -> SagemakerEndpoint:
        content_handler = SagemakerContentHandler()
        client = boto3.client("sagemaker-runtime", region_name=settings.AWS_REGION)
        # TODO - What should these parameters be?
        model_kwargs = {
            "temperature": 0.8,
            "max_new_tokens": 2048,
            "repetition_penalty": 1.03,
            "stop": ["###", "</s>"],
            "return_full_text": False,
        }
        sagemaker_endpoint = SagemakerEndpoint(
            endpoint_name=settings.SAGEMAKER_ENDPOINT_NAME,
            content_handler=content_handler,
            model_kwargs=model_kwargs,
            client=client,
        )
        return sagemaker_endpoint
