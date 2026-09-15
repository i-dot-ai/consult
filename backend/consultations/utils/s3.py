import boto3
from botocore.config import Config
from django.conf import settings

logger = settings.LOGGER


def get_s3_client(config: Config | None = None):
    config = config or Config()
    if not settings.ENVIRONMENT.upper() in ["LOCAL", "TEST"]:
        return boto3.client("s3", config=config)
