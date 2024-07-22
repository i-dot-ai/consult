import boto3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
import logging
import psutil
import time
import threading

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
def upload_file(file):
    """
    Uploads a file to an S3 bucket and returns the S3 URL of the uploaded file.

    Args:
        file: The file object to be uploaded.

    Returns:
        str: The S3 URL of the uploaded file.

    Raises:
        Exception: If there is an error uploading the file to S3.

    """
    timer = Timer()
    timer.time("S3 Upload - Starts")

    channel_layer = get_channel_layer()

    try:
        s3 = boto3.resource('s3')
        s3_bucket = s3.Bucket(settings.APP_BUCKET)
        key = file.name
        s3_bucket.upload_fileobj(file, file.name, Callback=ProgressPercentage(file, key))

        logging.info(f"Completed upload for {key}")
        
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        # TODO: handle the exception here, such as logging the error or raising it again

    s3_url = f"https://{settings.APP_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{file.name}"

    timer.time("S3 Upload - Ends")

    return s3_url


class ProgressPercentage(object):
    """
    A class that tracks the progress of a file upload and sends the progress to a WebSocket.

    Args:
        file (File): The file being uploaded.
        key (str): The key or name of the file.

    Attributes:
        _filename (str): The name of the file.
        _size (int): The size of the file in bytes.
        _seen_so_far (int): The number of bytes seen so far.
        _lock (threading.Lock): A lock to ensure thread safety.

    """

    def __init__(self, file, key):
        self._filename = key
        self._size = file.size
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        """
        Update the progress and send it to the WebSocket.

        Args:
            bytes_amount (int): The number of bytes processed.

        """
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            logging.info(f"Progress: {percentage}% for {self._filename}")

            # Send progress to WebSocket
            self.new_method(percentage)

    def new_method(self, percentage):
        # Get the channel layer
        channel_layer = get_channel_layer()

        # Send the progress to the WebSocket group "upload_progress"
        async_to_sync(channel_layer.group_send)(
            "upload_progress",
            {
                "type": "upload.progress",
                "percentage": percentage,
            }
        )
