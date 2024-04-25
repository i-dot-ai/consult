import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")


def check_and_launch_sagemaker(func):
    def wrapper(*args, **kwargs):
        sagemaker = boto3.client("sagemaker")
        endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME", None)
        if not endpoint_name:
            return func(*args, **kwargs)
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
