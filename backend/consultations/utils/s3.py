import boto3
from botocore.config import Config
from django.conf import settings

logger = settings.LOGGER

def get_s3_client():
    if settings.ENVIRONMENT.upper() in ["LOCAL", "TEST"]:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ADDRESS,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,  # pragma: allowlist secret
            config=Config(signature_version="s3v4")
        )
        buckets = s3_client.list_buckets()["Buckets"]
        if not any(bucket["Name"] == settings.AWS_BUCKET_NAME for bucket in buckets):
            logger.info(
                "Bucket not found, creating - {bucket_name}",
                bucket_name=settings.AWS_BUCKET_NAME,
            )
            s3_client.create_bucket(Bucket=settings.AWS_BUCKET_NAME)
    else:
        s3_client = boto3.client("s3")
    return s3_client
