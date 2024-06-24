import datetime
import logging
import time

import boto3
from django.conf import settings

logger = logging.getLogger("pipeline")


def check_and_launch_sagemaker(func):
    initialized = False

    def wrapper(*args, **kwargs):
        nonlocal initialized

        sagemaker_client = boto3.client("sagemaker", region_name=settings.AWS_REGION)
        endpoint_name = settings.SAGEMAKER_ENDPOINT_NAME
        try:
            sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        except boto3.exceptions.botocore.exceptions.ClientError as _:
            sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_name,
            )
        start_time = datetime.datetime.now()
        endpoint_status = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)[
            "EndpointStatus"
        ]
        if endpoint_status != "InService":
            logger.info("Endpoint is being created...")

        while endpoint_status != "InService":
            time.sleep(15)
            duration = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(f"Seconds elapsed {duration}.")
            if duration > 60 * 15:
                raise RuntimeError(f"Error creating Sagemaker endpoint after {duration} seconds.")
            endpoint_status = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)[
                "EndpointStatus"
            ]
        if not initialized:
            logger.info(f"Endpoint {endpoint_name} is 'InService' i.e. ready to use.")
            initialized = True
        return func(*args, **kwargs)

    return wrapper
