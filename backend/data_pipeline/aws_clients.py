"""
Boto3 client factories for AWS services used by the data pipeline.

Each factory reads an optional endpoint URL from Django settings, allowing
calls to be redirected to LocalStack in local/test environments while using
real AWS endpoints in deployed environments (where the setting is None).

Keeping these separate from the S3/MinIO client is intentional: S3 is handled
by django-storages using MINIO_ENDPOINT, so a global AWS_ENDPOINT_URL would
conflict. Instead, each service has its own endpoint setting:

    BATCH_ENDPOINT_URL  — controls boto3.client("batch")
    EVENTS_ENDPOINT_URL — controls boto3.client("events")

Both default to None, which lets boto3 resolve real AWS endpoints normally.
"""

import boto3
from django.conf import settings


def get_batch_client():
    """
    Return a boto3 Batch client.

    Points to LocalStack when BATCH_ENDPOINT_URL is set (local/test envs),
    or to real AWS when the setting is None (deployed envs).
    """
    kwargs = {}
    if endpoint_url := getattr(settings, "BATCH_ENDPOINT_URL", None):
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("batch", **kwargs)


def get_events_client():
    """
    Return a boto3 EventBridge client.

    Points to LocalStack when EVENTS_ENDPOINT_URL is set (local/test envs),
    or to real AWS when the setting is None (deployed envs).
    """
    kwargs = {}
    if endpoint_url := getattr(settings, "EVENTS_ENDPOINT_URL", None):
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("events", **kwargs)
