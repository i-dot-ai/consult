"""
Centralized boto3 client factory for S3 and other AWS services.

Automatically configures boto3 clients to use MinIO for local/test environments
and AWS S3 for production environments based on the ENVIRONMENT setting.
"""

import boto3
from botocore.config import Config
from django.conf import settings


def get_s3_client(**kwargs):
    """
    Create and return a boto3 S3 client configured for the current environment.

    In local/test environments (ENVIRONMENT='local' or 'test'):
    - Connects to MinIO using MINIO_ENDPOINT_URL
    - Uses explicit AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY credentials
    - Configures S3v4 signature version

    In production environments (ENVIRONMENT='dev', 'preprod', 'prod'):
    - Connects to AWS S3 using IAM role credentials
    - No explicit endpoint or credentials needed

    Args:
        **kwargs: Additional keyword arguments to pass to boto3.client()

    Returns:
        boto3.S3.Client: Configured S3 client
    """
    environment = getattr(settings, "ENVIRONMENT", "").lower()

    # Local/Test: Use MinIO
    if environment in ["local", "test"]:
        minio_endpoint = settings.MINIO_ENDPOINT_URL
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY

        # Filter out any endpoint_url, credentials, or config from kwargs
        # to avoid conflicts with our MinIO configuration
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["endpoint_url", "aws_access_key_id", "aws_secret_access_key", "config"]
        }

        client = boto3.client(
            "s3",
            endpoint_url=minio_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            **filtered_kwargs,
        )
        return client

    # Production: Use AWS S3 with IAM roles
    else:
        return boto3.client("s3", **kwargs)


def get_batch_client(**kwargs):
    """
    Create and return a boto3 Batch client.

    Note: Batch is only used in production environments. For local/test,
    this will still attempt to connect to AWS Batch (batch jobs don't run locally).

    Args:
        **kwargs: Additional keyword arguments to pass to boto3.client()

    Returns:
        boto3.Batch.Client: Configured Batch client
    """
    return boto3.client("batch", **kwargs)
