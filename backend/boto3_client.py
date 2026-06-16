"""
Centralized boto3 client factory for S3 and other AWS services.

Automatically configures boto3 clients to use MinIO for local/test environments
and AWS S3 for production environments.
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

_s3_client = None


def _get_s3_client():
    """
    Get or create a boto3 S3 client singleton.
    
    Automatically handles environment detection:
    - ENVIRONMENT=local or test → connects to MinIO
    - ENVIRONMENT=dev/preprod/prod → connects to AWS S3 using IAM role
    
    In local/test environments, ensures the bucket exists.
    
    Returns:
        boto3.S3.Client: Configured S3 client
    """
    global _s3_client
    
    if _s3_client is None:
        logger = settings.LOGGER
        environment = settings.ENVIRONMENT.lower()
        
        if environment in ["local", "test"]:
            # MinIO configuration for local/test
            _s3_client = boto3.client(
                "s3",
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.AWS_REGION,
                config=Config(signature_version="s3v4"),
            )
            
            # Ensure bucket exists in local/test environments
            bucket_name = settings.AWS_BUCKET_NAME
            try:
                _s3_client.head_bucket(Bucket=bucket_name)
                logger.info(
                    "Bucket already exists: {bucket_name}",
                    bucket_name=bucket_name,
                )
            except ClientError:
                logger.info(
                    "Creating bucket for local/test environment: {bucket_name}",
                    bucket_name=bucket_name,
                )
                try:
                    _s3_client.create_bucket(Bucket=bucket_name)
                except Exception as e:
                    logger.warning(
                        "Failed to create bucket - {bucket_name}: {error}",
                        bucket_name=bucket_name,
                        error=str(e),
                    )
        else:
            # AWS S3 with IAM role for production
            _s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    
    return _s3_client


def get_s3_client(**kwargs):
    """
    Create and return a boto3 S3 client configured for the current environment.
    
    In local/test environments (ENVIRONMENT='local' or 'test'):
    - Connects to MinIO using MINIO_ENDPOINT
    - Uses explicit MINIO_ACCESS_KEY and MINIO_SECRET_KEY credentials
    - Configures S3v4 signature version
    
    In production environments (ENVIRONMENT='dev', 'preprod', 'prod'):
    - Connects to AWS S3 using IAM role credentials
    - No explicit endpoint or credentials needed
    
    Args:
        **kwargs: Additional keyword arguments (currently unused, reserved for future use)
    
    Returns:
        boto3.S3.Client: Configured S3 client
    """
    return _get_s3_client()


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
