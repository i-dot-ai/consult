import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)



# AWS Batch client
batch_client = boto3.client("batch")


def lambda_handler(event, context):
    """
    Lambda handler to process a single SQS message and submit job to AWS Batch.
    """
    logger.info(f"Received event with {len(event['Records'])} records")

    records = event.get("Records", [])

    if len(records) != 1:
        raise ValueError(
            "Expected exactly 1 SQS record, but received {n_records}", n_records=len(records)
        )

    record = records[0]
    logger.info("Processing SQS record")

    message_body = record["body"]
    try:
        message_data = json.loads(message_body)
        logger.info(f"Parsed message: {message_data}")
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON in message body: {msg}", {e})

    process_message(message_data)

    logger.info("Successfully processed SQS record")


def process_message(message_data):
    """
    Submits a job to AWS Batch based on message_data dict.
    Expected keys:
    - jobName
    - jobQueue
    - jobDefinition
    - containerOverrides
    - jobType
    - userId
    - parameters (optional, for backward compatibility)
    """
    if not isinstance(message_data, dict):
        raise ValueError("Message data must be a JSON object")

    job_name = message_data.get("jobName")
    job_queue = message_data.get("jobQueue")
    job_definition = message_data.get("jobDefinition")
    user_id = message_data.get("userId")
    container_overrides = message_data.get("containerOverrides", {})
    job_parameters = message_data.get("parameters", {})

    if not job_queue:
        raise ValueError("Missing required field: jobQueue")
    if not job_definition:
        raise ValueError("Missing required field: jobDefinition")

    # Prepare the submit_job kwargs
    submit_job_kwargs = {
        "jobName": job_name,
        "jobQueue": job_queue,
        "jobDefinition": job_definition,
        "userId": user_id,
    }

    # Add containerOverrides if present
    if container_overrides:
        submit_job_kwargs["containerOverrides"] = container_overrides
        logger.info(f"Using container overrides: {container_overrides}")

    # Add parameters if present (for backward compatibility)
    if job_parameters:
        submit_job_kwargs["parameters"] = job_parameters
        logger.info(f"Using parameters: {job_parameters}")

    logger.info(f"Submitting AWS Batch job: {job_name}")
    logger.info(f"user id: {user_id}")
    response = batch_client.submit_job(**submit_job_kwargs)

    job_id = response["jobId"]
    logger.info(f"Successfully submitted job: {job_id} for jobName: {job_name}")
