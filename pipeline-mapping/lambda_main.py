import json
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Batch client
batch_client = boto3.client('batch')

def lambda_handler(event, context):
    """
    Lambda handler to submit a job to AWS Batch
    
    Expected event structure:
    {
        "jobName": "my-batch-job",
        "jobQueue": "my-job-queue", 
        "jobDefinition": "my-job-definition",
        "parameters": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    """
    
    try:
        # Extract job details from event
        job_name = event.get('jobName', 'lambda-batch-job')
        job_queue = event.get('jobQueue')
        job_definition = event.get('jobDefinition')
        job_parameters = event.get('parameters', {})
        
        # Validate required fields
        if not job_queue:
            raise ValueError("jobQueue is required")
        if not job_definition:
            raise ValueError("jobDefinition is required")
        
        # Submit job to Batch
        response = batch_client.submit_job(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            parameters=job_parameters
        )
        
        job_id = response['jobId']
        logger.info(f"Successfully submitted job: {job_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job submitted successfully',
                'jobId': job_id,
                'jobName': job_name,
                'jobQueue': job_queue,
                'jobDefinition': job_definition
            })
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Bad Request',
                'message': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f"Error submitting batch job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to submit batch job'
            })
        }