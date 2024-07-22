import logging
import boto3
import json
from django.conf import settings
from consultation_analyser.consultations.upload_consultation import upload_consultation
from io import BytesIO
from django_rq import get_queue
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from django.http import HttpRequest
from asgiref.sync import async_to_sync


logger = logging.getLogger("Consultation Processing Task")


def process_json_from_s3(file, user):
    """
    Process a JSON file from an S3 bucket.

    Args:
        file (str): The path of the JSON file in the S3 bucket.
        user (str): The user performing the operation.

    """
    logger.info("Start")
    s3 = boto3.client('s3')
    bucket_name = settings.APP_BUCKET
    file_name = file.split('/')[-1]
    logger.info(f"Reading {file_name}")
    response = s3.get_object(Bucket=bucket_name, Key=file_name)

    file_content = response['Body'].read()
    file_handle = BytesIO(file_content)

    upload_consultation(file_handle, user)
    logger.info("End")




@csrf_exempt
def enqueue_job(file_name, user_name):
    """
    Enqueues a job to process a JSON file from S3.

    Args:
        file_name (str): The name of the JSON file to process.
        user_name (str): The name of the user who initiated the job.

    Returns:
        JsonResponse: A JSON response containing the job ID if successful, or an error message if unsuccessful.
    """
    logger.info("enqueue_job starts")
    queue = get_queue('default')
    try:
        job = queue.enqueue(process_json_from_s3, file_name, user_name)
        logger.info(f'Enqueued job with ID: {job.id}')
        # Get the channel layer
        channel_layer = get_channel_layer()

        # Send a group message to the "worker_status" group
        async_to_sync(channel_layer.group_send)(
            "worker_status",
            { 
            "type": "worker.status",
            "worker_job_id": job.id,
            }
        )
        job_status = queue.fetch_job(job.id).get_status()
        logger.info(f'Job Status: {job_status}')
        return JsonResponse({'job_id': job.id})
    except Exception as e:
        logger.error(f'Error enqueuing job: {e}')
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def get_job_status(request: HttpRequest, job_id):
    """
    Retrieves the status of a job from the default queue.

    Args:
        request (HttpRequest): The HTTP request object.
        job_id (str): The ID of the job to retrieve the status for.

    Returns:
        JsonResponse: A JSON response containing the job status, result, and meta information.
            If the job is not found, an error message is included in the response.
    """
    queue = get_queue('default')
    job = queue.fetch_job(job_id)

    if job:
        status = job.get_status()
        response_data = {
            'id': job.id,
            'status': status,
            'result': job.result,
            'meta': job.meta,
        }
    else:
        response_data = {'error': 'Job not found'}

    return JsonResponse(response_data)
