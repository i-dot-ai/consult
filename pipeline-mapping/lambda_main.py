import json
import logging
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Batch client
batch_client = boto3.client('batch')

def lambda_handler(event, context):
    """
    Lambda handler to process SQS messages and submit jobs to AWS Batch
    """
    logger.info(f"Received event with {len(event['Records'])} records")

    success_count = 0
    failure_count = 0

    for record in event['Records']:
        try:
            message_body = record['body']
            try:
                message_data = json.loads(message_body)
                logger.info(f"Parsed message: {message_data}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON, treating as raw text: {message_body}")
                message_data = message_body  # Could skip this if your messages are always JSON

            process_message(message_data)
            success_count += 1

        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            failure_count += 1
            # Letting it raise here would cause all messages to be retried. We handle gracefully.
            # To force retry of individual messages, raise here instead.

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {success_count} successfully, {failure_count} failed.'
        })
    }


def process_message(message_data):
    """
    Submits a job to AWS Batch based on message_data dict.
    Expected keys:
    - jobName
    - jobQueue
    - jobDefinition
    - parameters (optional)
    """
    if not isinstance(message_data, dict):
        raise ValueError("Message data must be a JSON object")

    job_name = message_data.get('jobName', 'lambda-batch-job')
    job_queue = message_data.get('jobQueue')
    job_definition = message_data.get('jobDefinition')
    job_parameters = message_data.get('parameters', {})

    if not job_queue:
        raise ValueError("Missing required field: jobQueue")
    if not job_definition:
        raise ValueError("Missing required field: jobDefinition")

    logger.info(f"Submitting AWS Batch job: {job_name}")
    response = batch_client.submit_job(
        jobName=job_name,
        jobQueue=job_queue,
        jobDefinition=job_definition,
        parameters=job_parameters
    )

    job_id = response['jobId']
    logger.info(f"Successfully submitted job: {job_id} for jobName: {job_name}")
