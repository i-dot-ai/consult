import boto3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
import logging
import psutil
import time

logger = logging.getLogger("upload")

class Timer:
    def __init__(self):
        self.last_time = time.time()

    def time(self, event):
        abs = time.time()
        delta = abs - self.last_time
        used_mb = psutil.Process().memory_info().rss / 1024**2

        self.last_time = abs
        self.last_delta = delta

        logline = (abs, delta, used_mb, event)
        logger.info(f"{logline}")


@csrf_exempt
def upload_file(file, channel_name):

    timer = Timer()
    timer.time("S3 Upload - Starts")

    channel_layer = get_channel_layer()

    def upload_progress(bytes_amount):
        progress = (bytes_amount / file.size) * 100
        async_to_sync(channel_layer.group_send)(
            channel_name,
            {
                'type': 'send_progress',
                'progress': progress,
            }
        )

    try:
        s3 = boto3.resource('s3')
        s3_bucket = s3.Bucket(settings.APP_BUCKET)
        s3_bucket.upload_fileobj(file, file.name)
        
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        # TODO: handle the exception here, such as logging the error or raising it again

    s3_url = f"https://{settings.APP_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{file.name}"

    timer.time("S3 Upload - Ends")

    return s3_url