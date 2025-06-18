import json
import urllib3
import os
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to send Slack notifications for AWS Batch job state changes
    """
    try:
        # Get Slack webhook URL from environment variable
        slack_webhook_url = "https://hooks.slack.com/services/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"
        environment = os.environ.get('ENVIRONMENT', 'unknown')
        
        if not slack_webhook_url:
            logger.error("SLACK_WEBHOOK_URL environment variable not set")
            return {
                'statusCode': 400,
                'body': json.dumps('Slack webhook URL not configured')
            }
        
        # Log the incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract batch job details from EventBridge event
        detail = event.get('detail', {})
        job_name = detail.get('jobName', 'Unknown Job')
        job_id = detail.get('jobId', 'Unknown ID')
        job_status = detail.get('jobStatus', 'Unknown Status')
        job_queue = detail.get('jobQueue', 'Unknown Queue')
        job_definition = detail.get('jobDefinition', 'Unknown Definition')
        reason = detail.get('statusReason', '')
        
        # Get timestamp from event or use current time
        event_time = event.get('time', datetime.utcnow().isoformat())
        
        # Create appropriate message based on status
        color = get_color_for_status(job_status)
        message = create_slack_message(
            job_name, job_id, job_status, job_queue, 
            job_definition, reason, color, event_time, environment
        )
        
        # Send to Slack
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            slack_webhook_url,
            body=json.dumps(message).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status == 200:
            logger.info(f"Successfully sent Slack notification for job {job_name} with status {job_status}")
            return {
                'statusCode': 200,
                'body': json.dumps(f'Notification sent for job {job_name} with status {job_status}')
            }
        else:
            logger.error(f"Failed to send Slack notification. Status: {response.status}, Response: {response.data}")
            return {
                'statusCode': response.status,
                'body': json.dumps(f'Failed to send notification. Slack API returned status {response.status}')
            }
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing event: {str(e)}')
        }

def get_color_for_status(status):
    """Return color code for different job statuses"""
    status_colors = {
        'SUBMITTED': '#36a64f',   # Green
        'PENDING': '#808080',     # Gray
        'RUNNABLE': '#ffaa00',    # Orange
        'STARTING': '#ffaa00',    # Orange
        'RUNNING': '#0099cc',     # Blue
        'SUCCEEDED': '#2eb886',   # Dark green
        'FAILED': '#ff0000',      # Red
        'TIMEOUT': '#ff6600',     # Dark orange
    }
    return status_colors.get(status.upper(), '#808080')

def get_status_emoji(status):
    """Return emoji for different job statuses"""
    status_emojis = {
        'SUBMITTED': ':white_check_mark:',
        'PENDING': ':clock1:',
        'RUNNABLE': ':hourglass_flowing_sand:',
        'STARTING': ':rocket:',
        'RUNNING': ':gear:',
        'SUCCEEDED': ':tada:',
        'FAILED': ':x:',
        'TIMEOUT': ':warning:'
    }
    return status_emojis.get(status.upper(), ':question:')

def format_job_definition(job_definition):
    """Extract job definition name from ARN"""
    if ':' in job_definition:
        # It's an ARN, extract the name
        return job_definition.split('/')[-1].split(':')[0]
    return job_definition

def create_slack_message(job_name, job_id, status, job_queue, job_definition, reason, color, event_time, environment):
    """Create formatted Slack message"""
    
    emoji = get_status_emoji(status)
    formatted_job_def = format_job_definition(job_definition)
    
    # Parse and format timestamp
    try:
        dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = event_time
    
    # Create the base message
    message = {
        "text": f"AWS Batch Job {status.title()} - {job_name}",
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} AWS Batch Job {status.title()}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Job Name:*\n{job_name}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{status}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Job ID:*\n`{job_id}`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Environment:*\n{environment.upper()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Queue:*\n{job_queue}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Job Definition:*\n{formatted_job_def}"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Add failure reason if job failed
    if status.upper() == 'FAILED' and reason:
        message["attachments"][0]["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Failure Reason:*\n```{reason[:500]}{'...' if len(reason) > 500 else ''}```"
            }
        })
    
    # Add AWS Console link
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    console_url = f"https://console.aws.amazon.com/batch/v2/home?region={aws_region}#jobs/detail/{job_id}"
    
    message["attachments"][0]["blocks"].append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View in AWS Console"
                },
                "url": console_url,
                "style": "primary" if status.upper() == 'FAILED' else None
            }
        ]
    })
    
    # Add timestamp
    message["attachments"][0]["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Time: {formatted_time}"
            }
        ]
    })
    
    return message