import json
import os

import urllib3
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import (
    ContextEnrichmentType,
    ExecutionEnvironmentType,
)
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat

http = urllib3.PoolManager()

logger = StructuredLogger(
    level="info",
    options={
        "execution_environment": ExecutionEnvironmentType.LAMBDA,
        "log_format": LogOutputFormat.JSON,
    },
)

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

MESSAGE_TITLE = {
    "FIND_THEMES": {
        "RUNNING": "🚀 Finding themes for",
        "SUCCEEDED": "✅ Found themes for",
        "FAILED": "❌ Failed to find themes for",
    },
    "ASSIGN_THEMES": {
        "RUNNING": "🚀 Assigning themes for",
        "SUCCEEDED": "✅ Assigned themes for",
        "FAILED": "❌ Failed to assign themes for",
    },
}


def send_slack_message(job: dict, consultation: dict, environment: str, user_id: str):
    message_title = (
        f"{MESSAGE_TITLE[job['type']][job['status']]} {consultation['name']}"
    )

    region = os.environ.get("LAMBDA_AWS_REGION", "eu-west-2")
    bucket = os.environ.get("AWS_BUCKET_NAME", "consult-data")

    job_url = f"https://console.aws.amazon.com/batch/home?region={region}#jobs/detail/{job['id']}"

    if job["type"] == "FIND_THEMES":
        s3_path = f"app_data/consultations/{consultation['code']}/outputs/sign_off/"
    else:
        s3_path = f"app_data/consultations/{consultation['code']}/outputs/mapping/"

    s3_url = f"https://s3.console.aws.amazon.com/s3/buckets/{bucket}?prefix={s3_path}&region={region}"

    message = {
        "text": message_title,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": message_title}},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Environment:*\n{environment}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Consultation:*\n{consultation['code']}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*User ID:*\n{user_id}",
                    },
                    {"type": "mrkdwn", "text": f"*Job ID:*\n`{job['id']}`"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View job in AWS",
                        },
                        "url": job_url,
                    }
                ],
            },
        ],
    }

    if job["status"] == "SUCCEEDED":
        # Add S3 button to the actions block
        blocks = message["blocks"]
        assert isinstance(blocks, list)
        actions_block = blocks[2]
        assert isinstance(actions_block, dict)
        elements = actions_block["elements"]
        assert isinstance(elements, list)
        elements.append(
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View data in S3",
                },
                "url": s3_url,
            }
        )

    encoded_msg = json.dumps(message).encode("utf-8")
    if SLACK_WEBHOOK_URL is None:
        raise ValueError("SLACK_WEBHOOK_URL environment variable is required")

    response = http.request(
        "POST",
        SLACK_WEBHOOK_URL,
        body=encoded_msg,
        headers={"Content-Type": "application/json"},
    )

    if response.status != 200:
        response_data = (
            response.data.decode("utf-8") if response.data else "No response data"
        )
        error_message = (
            f"Slack webhook failed with status {response.status}: {response_data}"
        )
        raise Exception(error_message)


def lambda_handler(event, context):
    """
    Lambda handler for sending Slack notifications, triggered by EventBridge,
    when AWS Batch job changes state.
    """
    logger.refresh_context([{"type": ContextEnrichmentType.LAMBDA, "object": context}])
    logger.set_context_field("execution_context", os.environ.get("EXECUTION_CONTEXT", "lambda"))

    logger.info("Received event: {event}", event=json.dumps(event))

    try:
        detail = event["detail"]
        parameters = detail["parameters"]

        job = {
            "id": detail["jobId"],
            "status": detail["status"],
            "type": parameters["job_type"],
        }
        consultation = {
            "name": parameters["consultation_name"],
            "code": parameters["consultation_code"],
        }
        environment = os.environ.get("ENVIRONMENT", "unknown")
        user_id = parameters["user_id"]

        logger.set_context_field("batch_job_name", detail.get("jobName", job["type"]))
        logger.set_context_field("consultation_code", consultation["code"])

        send_slack_message(job, consultation, environment, user_id)

        logger.info("✅ Slack message sent")

    except Exception:
        logger.exception("Failed to send Slack notification")
        raise
