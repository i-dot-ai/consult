import json
import logging
import os

import redis  # type: ignore
import urllib3
from rq import Queue

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

http = urllib3.PoolManager()


def lambda_handler(event, context):
    """
    Lambda function triggered by EventBridge when AWS Batch job completes
    """

    # Extract batch job details
    detail = event.get("detail", {})
    job_name = detail.get("jobName", "unknown")
    job_status = detail.get("status", "Unknown Status")

    parameters = detail.get("parameters", {})
    consultation_name = parameters.get("consultation_name", "unknown")
    mapping_date = parameters.get("mappingDate", "unknown")
    user_id = parameters.get("userId", "unknown")
    consultation_code = parameters.get("consultation_code", "unknown")

    logger.info(f"Batch job '{job_name}' completed with status: {job_status}")

    logger.info(f"Received event for job: {job_name}")
    logger.info(f"Job status: {job_status}")
    logger.info(f"Consultation name: {consultation_name}")
    logger.info(f"Mapping date: {mapping_date}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Consultation code: {consultation_code}")

    # Only process successful jobs
    if job_status != "SUCCEEDED":
        logger.info(f"Skipping job with status: {job_status}")
        return {"statusCode": 200, "body": "Job not successful, skipping"}

    # Validate required parameters
    if not all([consultation_name, consultation_code, mapping_date, user_id]):
        error_msg = f"Missing consultation parameters: name={consultation_name}, consultation_code={consultation_code}, mapping_date={mapping_date}, user_id={user_id}"
        logger.error(error_msg)
        return {"statusCode": 400, "body": error_msg}

    try:
        logger.info("=== RQ JOB SETUP ===")

        # Connect to Redis
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))

        logger.info(f"Connecting to Redis: {redis_host}:{redis_port}")

        redis_conn = redis.Redis(
            host=redis_host, port=redis_port, socket_timeout=30, socket_connect_timeout=30
        )

        # Test Redis connection
        logger.info("Testing Redis connection...")
        ping_result = redis_conn.ping()
        logger.info(f"✅ Redis PING result: {ping_result}")

        # Create RQ queue
        queue_name = "default"
        queue = Queue(queue_name, connection=redis_conn)

        logger.info(f"Created RQ queue: {queue_name}")

        # Enqueue the RQ job with all parameters
        logger.info("Enqueueing RQ job...")
        job = queue.enqueue(
            "consultation_analyser.ingest.jobs.consultations.import_consultation_job",
            consultation_name,
            consultation_code,
            user_id,
            mapping_date,
        )

        logger.info("✅ RQ job enqueued successfully!")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Job status: {job.get_status()}")

        # Check queue length
        queue_length = len(queue)
        logger.info(f"Queue '{queue_name}' now has {queue_length} jobs")

        # Send Slack notification
        try:
            slack_message = create_slack_success_message(
                consultation_name, consultation_code, mapping_date, job.id
            )
            send_slack_message(slack_message)
            slack_success = True
            logger.info("✅ Slack notification sent successfully")
        except Exception as slack_error:
            logger.warning(f"⚠️ Failed to send Slack notification: {slack_error}")
            slack_success = False

        success_msg = f"Successfully queued RQ job {job.id} for consultation: {consultation_name}"
        logger.info(success_msg)

        return {
            "statusCode": 200,
            "body": {
                "message": success_msg,
                "job_id": job.id,
                "queue": queue_name,
                "queue_length": queue_length,
                "slack_notification_sent": slack_success,
            },
        }

    except Exception as e:
        error_msg = f"Failed to trigger consultation import: {str(e)}"
        logger.error(f"ERROR: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")

        # Send error notification to Slack
        try:
            slack_error_message = create_slack_error_message(
                error_msg, consultation_name, consultation_code
            )
            send_slack_message(slack_error_message)
            logger.info("✅ Slack error notification sent successfully")
        except Exception as slack_error:
            logger.warning(f"⚠️ Failed to send Slack error notification: {slack_error}")

        return {"statusCode": 500, "body": error_msg}


def create_slack_success_message(consultation_name, consultation_code, mapping_date, job_id):
    """
    Create Slack message payload for successful job
    """
    return {
        "text": "🎉 Consultation Import Job Queued Successfully",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "🎉 Import Job Queued"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Consultation Name:*\n{consultation_name}"},
                    {"type": "mrkdwn", "text": f"*Consultation Code:*\n{consultation_code}"},
                    {"type": "mrkdwn", "text": f"*Mapping Date:*\n{mapping_date}"},
                ],
            },
            {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Job ID:*\n`{job_id}`"}]},
        ],
    }


def create_slack_error_message(error_msg, consultation_name, consultation_code):
    """
    Create Slack message payload for failed job
    """
    return {
        "text": "❌ Consultation Import Job Failed",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "❌ Consultation Import Job Failed"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Consultation Name:*\n{consultation_name}"},
                    {"type": "mrkdwn", "text": f"*Consultation Code:*\n{consultation_code}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Error Details:*\n```{error_msg}```"},
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🔍 Please check the Lambda logs for more details"}
                ],
            },
        ],
    }


def send_slack_message(message):
    """
    Send message to Slack webhook
    """
    logger.info("=== SLACK NOTIFICATION SETUP ===")

    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable is not set")

    logger.info("Preparing to send Slack notification...")
    encoded_msg = json.dumps(message).encode("utf-8")
    logger.info(f"Message payload size: {len(encoded_msg)} bytes")

    logger.info("Sending HTTP request to Slack...")
    response = http.request(
        "POST", SLACK_WEBHOOK_URL, body=encoded_msg, headers={"Content-Type": "application/json"}
    )

    logger.info(f"Slack response status: {response.status}")
    if response.data:
        logger.info(f"Slack response data: {response.data.decode('utf-8')}")

    if response.status != 200:
        raise Exception(
            f"Slack request failed with status {response.status}: {response.data.decode('utf-8') if response.data else 'No response data'}"
        )
