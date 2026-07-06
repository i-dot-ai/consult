import boto3
from botocore.config import Config
from django.conf import settings

logger = settings.LOGGER

def get_s3_client(config: Config | None = None):
    config = config or Config()
    if settings.ENVIRONMENT.upper() in ["LOCAL", "TEST"]:
        base_config = Config(signature_version="s3v4")
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ADDRESS,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,  # pragma: allowlist secret
            config=base_config.merge(config),
        )
    else:
        s3_client = boto3.client("s3", config=config)
    return s3_client
