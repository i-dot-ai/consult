import json
import logging
import os
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

http = urllib3.PoolManager()

def create_slack_message(job_name, status, job_id, subdir):
    region = os.environ.get("AWS_REGION", "us-east-1")

    # Friendly, branded titles
    status_title_map = {
        "SUCCEEDED": "✅ Themefinder Job Completed",
        "RUNNING": "🚀 Themefinder Job Started",
        "FAILED": "❌ Themefinder Job Failed"
    }
    status_emoji_map = {
        "SUCCEEDED": "✅",
        "RUNNING": "🟢",
        "FAILED": "❌"
    }
    title = status_title_map.get(status, f"ℹ️ Themefinder Job {status}")
    emoji = status_emoji_map.get(status, "ℹ️")

    # AWS console URLs
    job_console_url = f"https://console.aws.amazon.com/batch/home?region={region}#jobs/detail/{job_id}"
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Consultation:*\n{subdir or 'N/A'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{emoji} *{status.title()}*"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Job Name:*\n{job_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Job ID:*\n`{job_id}`"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🖥️ View Job in Console",
                            "emoji": True
                        },
                        "url": job_console_url
                    }
                ]
            }
        ]
    }

    return message

def send_to_slack(message):
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL is not set")

    encoded_msg = json.dumps(message).encode("utf-8")
    response = http.request("POST", SLACK_WEBHOOK_URL, body=encoded_msg, headers={"Content-Type": "application/json"})

    if response.status != 200:
        raise Exception(f"Request to Slack returned error {response.status}, the response is:\n{response.data}")



def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        detail = event.get('detail', {})
        job_status = detail.get('status', 'Unknown Status')

        # Only proceed for SUCCEEDED or RUNNING
        if job_status not in ['SUCCEEDED', 'RUNNING']:
            logger.info(f"Ignoring job with status {job_status}")
            return {
                'statusCode': 200,
                'body': json.dumps(f"Ignored job with status {job_status}")
            }

        job_name = detail.get('jobName', 'Unknown Job')
        job_id = detail.get('jobId', 'Unknown ID')
        job_queue = detail.get('jobQueue', 'Unknown Queue')
        container = detail.get('container', {})
        command = container.get('command', [])

        subdir = None
        if command and "--subdir" in command:
            idx = command.index("--subdir")
            if idx + 1 < len(command):
                subdir = command[idx + 1]


        slack_message = create_slack_message(job_name, job_status, job_id, subdir)

        send_to_slack(slack_message)

        return {
            'statusCode': 200,
            'body': json.dumps('Slack notification sent successfully')
        }

    except Exception as e:
        logger.error("Error processing event: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing event')
        }