import boto3
from botocore.config import Config

from settings.base import ENVIRONMENT, MINIO_ADDRESS, AWS_ACCESS_KEY, AWS_SECRET_KEY


def get_s3_client():
    if ENVIRONMENT.upper() in ["LOCAL"]:
        s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ADDRESS,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,  # pragma: allowlist secret
            config=Config(signature_version="s3v4")
        )
    else:
        s3_client = boto3.client("s3")
    return s3_client
