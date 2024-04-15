import logging
import os
from typing import Dict

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event: Dict, context):
    alarm_name: str = event["AlarmName"]
    sagemaker_endpoint_name = alarm_name[: alarm_name.find("_CPU_Low")]
    queue_name = os.environ["queue_name"]

    logger.info(f"Lambda started for alarm {alarm_name}, endpoint {sagemaker_endpoint_name} and queue {queue_name}")

    client = boto3.client("batch")
    jobs = client.list_jobs(jobQueue=queue_name)

    if not jobs["jobSummaryList"]:
        # No jobs found in the batch queue
        logger.info("No jobs found in the batch queue")
        # Shutdown alarm
        cloudwatch = boto3.resource("cloudwatch")
        alarm = cloudwatch.Alarm(alarm_name)
        alarm.load()
        alarm.delete()
        logger.info(f"Alarm {alarm_name} shut down")
        # Shutdown sagemaker
        sagemaker = boto3.client("sagemaker")
        sagemaker.delete_endpoint(EndpointName=sagemaker_endpoint_name)
        logger.info(f"Sagemaker endpoint {sagemaker_endpoint_name} deleted")
        return
    else:
        # Jobs found waiting in the batch queue
        logger.info(f"Jobs found in the {queue_name} queue, exiting lambda")
        return
