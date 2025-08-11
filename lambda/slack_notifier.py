import json
import logging
import os

import urllib3

from django.conf import settings

logger = settings.LOGGER
logger.setLevel(logging.INFO)

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

http = urllib3.PoolManager()


def create_slack_message(job_name, status, job_id, job_type, subdir):
    region = os.environ.get("LAMBDA_AWS_REGION")

    if job_type == "THEMEFINDER":
        job_type_name = "Themefinder"
    elif job_type == "SIGNOFF":
        job_type_name = "Sign-off"
    elif not job_type or job_type.strip() == "":
        logger.error("Job type is blank or null for job_id: {job_id}", job_id=job_id)
        raise ValueError("Job type cannot be blank or null")
    else:
        logger.error(
            "Unknown job type: {job_type} for job_id: {job_id}", job_type=job_type, job_id=job_id
        )
        raise ValueError(f"Unknown job type: {job_type}")

    status_title_map = {
        "SUCCEEDED": f"✅ {job_type_name} Job Completed",
        "RUNNING": f"🚀 {job_type_name} Job Started",
        "FAILED": f"❌ {job_type_name} Job Failed",
    }
    status_emoji_map = {"SUCCEEDED": "✅", "RUNNING": "🟢", "FAILED": "❌"}
    title = status_title_map.get(status, f"ℹ️ {job_type_name} Job {status}")
    emoji = status_emoji_map.get(status, "ℹ️")

    # AWS console URLs
    job_console_url = (
        f"https://console.aws.amazon.com/batch/home?region={region}#jobs/detail/{job_id}"
    )

    message = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": title, "emoji": True}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Consultation:*\n{subdir or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{emoji} *{status.title()}*"},
                    {"type": "mrkdwn", "text": f"*Job Name:*\n{job_name}"},
                    {"type": "mrkdwn", "text": f"*Job ID:*\n`{job_id}`"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🖥️ View Job in Console",
                            "emoji": True,
                        },
                        "url": job_console_url,
                    }
                ],
            },
        ]
    }

    return message


def send_to_slack(message):
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL is not set")

    encoded_msg = json.dumps(message).encode("utf-8")
    response = http.request(
        "POST", SLACK_WEBHOOK_URL, body=encoded_msg, headers={"Content-Type": "application/json"}
    )

    if response.status != 200:
        raise Exception(
            f"Request to Slack returned error {response.status}, the response is:\n{response.data}"
        )


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        detail = event.get("detail", {})
        job_status = detail.get("status", "Unknown Status")

        # Only proceed for SUCCEEDED or RUNNING
        if job_status not in ["SUCCEEDED", "RUNNING", "FAILED"]:
            logger.info("Ignoring job with status {job_status}", job_status=job_status)
            return {"statusCode": 200, "body": json.dumps(f"Ignored job with status {job_status}")}

        job_name = detail.get("jobName", "Unknown Job")
        job_id = detail.get("jobId", "Unknown ID")

        subdir, job_type = extract_job_details(detail, job_id)

        slack_message = create_slack_message(job_name, job_status, job_id, job_type, subdir)

        send_to_slack(slack_message)

    except Exception as e:
        logger.error("Error processing event: error", error=e)


def extract_job_details(detail, job_id):
    """
    Extract subdir and job_type from the Batch job details
    """
    subdir = "unknown"
    job_type = "unknown"

    try:
        # Try to get from the event detail (if available)
        container = detail.get("container", {})
        command = container.get("command", [])

        if command:  # Check if command exists and is not empty
            subdir, job_type = parse_command_args(command)
            logger.info(
                "Extracted job details: subdir={subdir}, job_type={job_type}",
                subdir=subdir,
                job_type=job_type,
            )
        else:
            logger.warning(f"No command found in container details for job {job_id}")

    except Exception as e:
        logger.warning(f"Could not extract job details: {e}")

    return subdir, job_type


def parse_command_args(command):
    """
    Parse command array to extract subdir and job_type
    Example: ["--subdir", "dwp", "--job-type", "THEMEFINDER"]
    """
    subdir = "unknown"
    job_type = "unknown"

    try:
        logger.debug("Parsing command: {command}", command=command)

        # Find --subdir value
        if "--subdir" in command:
            idx = command.index("--subdir")
            if idx + 1 < len(command):
                subdir = command[idx + 1]

        # Find --job-type value
        if "--job-type" in command:
            idx = command.index("--job-type")
            if idx + 1 < len(command):
                job_type = command[idx + 1]

        logger.info(
            "Parsed from command: subdir={subdir}, job_type={job_type}",
            subdir=subdir,
            job_type=job_type,
        )

    except Exception as e:
        logger.warning(f"Error parsing command args: {e}")

    return subdir, job_type
