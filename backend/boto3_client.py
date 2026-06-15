"""
Centralized boto3 client factory using i_dot_ai_utilities for S3 and other AWS services.

Automatically configures boto3 clients to use MinIO for local/test environments
and AWS S3 for production environments using the i_dot_ai_utilities.file_store module.
"""

import boto3
from django.conf import settings
from i_dot_ai_utilities.file_store.aws_s3.main import S3FileStore
from i_dot_ai_utilities.file_store.settings import Settings as FileStoreSettings

_file_store_client = None


def _get_file_store():
    """
    Get or create the i_dot_ai_utilities S3FileStore instance.
    
    The FileStore automatically handles MinIO vs AWS S3 based on environment variables:
    - ENVIRONMENT=local or test → connects to MinIO
    - ENVIRONMENT=dev/preprod/prod → connects to AWS S3
    
    In local/test environments, ensures the bucket exists.
    
    Returns:
        S3FileStore: Configured file store instance
    """
    global _file_store_client
    
    if _file_store_client is None:
        logger = settings.LOGGER
        file_store_settings = FileStoreSettings()
        _file_store_client = S3FileStore(
            logger=logger,
            settings=file_store_settings,
        )
        
        # Ensure bucket exists in local/test environments
        environment = file_store_settings.environment.lower()
        if environment in ["local", "test"]:
            bucket_name = settings.AWS_BUCKET_NAME
            try:
                buckets = _file_store_client.list_buckets()
                if not any(bucket["Name"] == bucket_name for bucket in buckets):
                    logger.info(
                        "Creating bucket for local/test environment: {bucket_name}",
                        bucket_name=bucket_name,
                    )
                    _file_store_client.create_bucket(name=bucket_name)
            except Exception as e:
                logger.warning(
                    "Failed to check/create bucket - {bucket_name}: {error}",
                    bucket_name=bucket_name,
                    error=str(e),
                )
    
    return _file_store_client


def get_s3_client(**kwargs):
    """
    Create and return a boto3 S3 client configured for the current environment.
    
    Uses i_dot_ai_utilities.file_store which automatically detects environment:
    
    In local/test environments (ENVIRONMENT='local' or 'test'):
    - Connects to MinIO using IAI_FS_MINIO_ADDRESS
    - Uses explicit IAI_FS_AWS_ACCESS_KEY_ID and IAI_FS_AWS_SECRET_ACCESS_KEY credentials
    - Configures S3v4 signature version
    
    In production environments (ENVIRONMENT='dev', 'preprod', 'prod'):
    - Connects to AWS S3 using IAM role credentials
    - No explicit endpoint or credentials needed
    
    Args:
        **kwargs: Additional keyword arguments (currently unused, reserved for future use)
    
    Returns:
        boto3.S3.Client: Configured S3 client from i_dot_ai_utilities
    """
    file_store = _get_file_store()
    return file_store.get_client()


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
