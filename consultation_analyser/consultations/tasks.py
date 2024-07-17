import logging
import boto3
import json
from django.conf import settings
from consultation_analyser.consultations.upload_consultation import upload_consultation
from io import BytesIO

logger = logging.getLogger("Consultation Processing Task")


def process_json_from_s3(file, user):
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
    