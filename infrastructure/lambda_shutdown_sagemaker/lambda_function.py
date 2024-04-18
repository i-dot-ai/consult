import logging
import os
from typing import Dict

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event: Dict, context):
    try:
        alarm_name: str = event["AlarmName"]
        sagemaker_endpoint_name = alarm_name[: alarm_name.find("_CPU_Low")]
        queue_name = os.environ["queue_name"]

        logger.info(f"Lambda started for alarm {alarm_name}, endpoint {sagemaker_endpoint_name} and queue {queue_name}")

        client = boto3.client("batch")
        jobs = client.list_jobs(jobQueue=queue_name)

        if not jobs["jobSummaryList"]:
            # No jobs found in the batch queue
            logger.info("No jobs found in the batch queue")
            # Shutdown sagemaker
            sagemaker = boto3.client("sagemaker")
            logger.info("Sagemaker client created")
            try:
                response = sagemaker.describe_endpoint(EndpointName=sagemaker_endpoint_name)
                endpoint_status = response["EndpointStatus"]
                if endpoint_status is not "InService":
                    logger.info(
                        f"Sagemaker endpoint {sagemaker_endpoint_name} status is not 'InService', try again once the status has changed. Exiting..."
                    )
            except boto3.exceptions.botocore.exceptions.ClientError as e:
                logger.info(
                    f"Sagemaker endpoint {sagemaker_endpoint_name} not found, assuming the endpoint is already shutdown. Exiting..."
                )
                return {
                    "message": f"Sagemaker endpoint {sagemaker_endpoint_name} not found, assuming the endpoint is already shutdown. Exiting..."
                }
            sagemaker.delete_endpoint(EndpointName=sagemaker_endpoint_name)
            logger.info(f"Sagemaker endpoint {sagemaker_endpoint_name} deleted")
            return {"message": f"Sagemaker endpoint {sagemaker_endpoint_name} deleted"}
        else:
            # Jobs found waiting in the batch queue
            logger.info(f"Jobs found in the {queue_name} queue, exiting lambda")
            return {"message": f"Jobs found in the {queue_name} queue, exiting lambda"}
    except Exception as ex:
        logger.error(f"Exception {ex} occurred")
        return {"message": f"General exception {ex} occurred. Exiting..."}
