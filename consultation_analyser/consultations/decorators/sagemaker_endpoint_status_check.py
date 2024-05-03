import logging

import boto3
from django.conf import settings

logger = logging.getLogger()
logger.setLevel("INFO")


def check_and_launch_sagemaker(func):
    def wrapper(*args, **kwargs):
        print(f"USE_SAGEMALER_LLM: {settings.USE_SAGEMAKER_LLM}")
        if not settings.USE_SAGEMAKER_LLM:
            return func(*args, **kwargs)
        sagemaker = boto3.client("sagemaker")
        endpoint_name = settings.SAGEMAKER_ENDPOINT_NAME
        try:
            sagemaker.describe_endpoint(EndpointName=endpoint_name)
            logger.info(f"Endpoint {endpoint_name} already exists. Skipping creation.")
        except boto3.exceptions.botocore.exceptions.ClientError as _:
            sagemaker.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_name,
            )
            logger.info(f"Endpoint {endpoint_name} has been created.")
        return func(*args, **kwargs)

    return wrapper
