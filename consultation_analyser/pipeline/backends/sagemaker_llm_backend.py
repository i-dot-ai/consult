import datetime
import json
import logging
import time

import boto3
from django.conf import settings
from langchain_community.llms import SagemakerEndpoint
from langchain_community.llms.sagemaker_endpoint import LLMContentHandler

from .langchain_llm_backend import LangchainLLMBackend

logger = logging.getLogger("pipeline")


class SagemakerFailureException(Exception):
    pass


def check_and_launch_sagemaker(func):
    initialized = False

    def wrapper(*args, **kwargs):
        nonlocal initialized

        sagemaker_client = boto3.client("sagemaker", region_name=settings.AWS_REGION)
        endpoint_name = settings.SAGEMAKER_ENDPOINT_NAME
        try:
            sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        except boto3.exceptions.botocore.exceptions.ClientError as _:
            logger.info("Endpoint is being created...")
            sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_name,
            )
        start_time = datetime.datetime.now()
        endpoint_details = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        endpoint_status = endpoint_details["EndpointStatus"]

        while endpoint_status != "InService":
            if endpoint_status == "Failed":
                raise SagemakerFailureException(endpoint_details)

            time.sleep(15)
            duration = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(f"Seconds elapsed {duration}")
            if duration > 60 * 15:
                raise RuntimeError(f"Error creating Sagemaker endpoint after {duration} seconds")
            endpoint_status = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)[
                "EndpointStatus"
            ]

        if not initialized:
            logger.info(f"Endpoint {endpoint_name} is 'InService' i.e. ready to use")
            initialized = True
        return func(*args, **kwargs)

    return wrapper


class SagemakerContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, inputs: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"inputs": inputs, "parameters": model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output) -> str:
        s = output.read().decode("utf-8")
        response_json = json.loads(s)
        return response_json[0]["generated_text"]


class SagemakerEndpointWithStartupWrapper(SagemakerEndpoint):
    @check_and_launch_sagemaker
    def _call(self, *args, **kwargs):
        return super()._call(*args, **kwargs)


class SagemakerLLMBackend(LangchainLLMBackend):
    def __init__(self):
        return super().__init__(self.__get_sagemaker_endpoint())

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
        sagemaker_endpoint = SagemakerEndpointWithStartupWrapper(
            endpoint_name=settings.SAGEMAKER_ENDPOINT_NAME,
            content_handler=content_handler,
            model_kwargs=model_kwargs,
            client=client,
        )
        return sagemaker_endpoint
