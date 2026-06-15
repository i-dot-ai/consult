import json
import re
from typing import Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from i_dot_ai_utilities.file_store.settings import Settings as FileStoreSettings

from boto3_client import get_s3_client

logger = settings.LOGGER
account_id = settings.AWS_ACCOUNT_ID


def _get_s3_resource():
    """
    Create and return a boto3 S3 resource configured for the current environment.
    Uses i_dot_ai_utilities settings to maintain consistency with get_s3_client().
    """
    file_store_settings = FileStoreSettings()
    environment = file_store_settings.environment.lower()

    if environment in ["local", "test"]:
        return boto3.resource(
            "s3",
            endpoint_url=file_store_settings.minio_address,
            aws_access_key_id=file_store_settings.aws_access_key_id,
            aws_secret_access_key=file_store_settings.aws_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
    else:
        return boto3.resource("s3")


def read_jsonl(
    bucket_name: str, key: str, s3_client=None, raise_if_missing: bool = True
) -> List[Dict]:
    """
    Read a JSONL file from S3 and return list of parsed objects.

    Args:
        bucket_name: S3 bucket name
        key: S3 key to JSONL file
        s3_client: Optional boto3 S3 client (creates new one if not provided)
        raise_if_missing: If False, return empty list instead of raising error

    Returns:
        List of parsed JSON objects (one per line)

    Raises:
        ClientError: If file doesn't exist and raise_if_missing=True
    """
    if s3_client is None:
        s3_client = get_s3_client()

    try:
        # Only include ExpectedBucketOwner if account_id is set (production environments)
        get_params = {"Bucket": bucket_name, "Key": key}
        if account_id:
            get_params["ExpectedBucketOwner"] = account_id
        response = s3_client.get_object(**get_params)
    except ClientError as e:
        if not raise_if_missing and e.response["Error"]["Code"] == "NoSuchKey":
            logger.info("File not found (skipping): {key}", key=key)
            return []
        raise

    objects = []
    for line in response["Body"].iter_lines():
        data = json.loads(line.decode("utf-8"))
        objects.append(data)

    return objects


def read_json(
    bucket_name: str, key: str, s3_client=None, raise_if_missing: bool = True
) -> Optional[Dict]:
    """
    Read a JSON file from S3 and return parsed object.

    Args:
        bucket_name: S3 bucket name
        key: S3 key to JSON file
        s3_client: Optional boto3 S3 client (creates new one if not provided)
        raise_if_missing: If False, return None instead of raising error

    Returns:
        Parsed JSON object or None if not found and raise_if_missing=False

    Raises:
        ClientError: If file doesn't exist and raise_if_missing=True
    """
    if s3_client is None:
        s3_client = get_s3_client()

    try:
        # Only include ExpectedBucketOwner if account_id is set (production environments)
        get_params = {"Bucket": bucket_name, "Key": key}
        if account_id:
            get_params["ExpectedBucketOwner"] = account_id
        response = s3_client.get_object(**get_params)
        data = json.loads(response["Body"].read())
        return data
    except ClientError as e:
        if not raise_if_missing and e.response["Error"]["Code"] == "NoSuchKey":
            logger.info("File not found (skipping): {key}", key=key)
            return None
        raise


def get_question_folders(inputs_path: str, bucket_name: str) -> List[str]:
    """
    Get all question_part_N folders from the inputs path.

    Args:
        inputs_path: S3 path to inputs folder (e.g., "app_data/consultations/CODE/inputs/")
        bucket_name: S3 bucket name

    Returns:
        Sorted list of question folder paths ending with /
    """
    s3 = _get_s3_resource()
    # Only include ExpectedBucketOwner if account_id is set (production environments)
    filter_params = {"Prefix": inputs_path}
    if account_id:
        filter_params["ExpectedBucketOwner"] = account_id
    objects = s3.Bucket(bucket_name).objects.filter(**filter_params)
    object_names_set = {obj.key for obj in objects}

    # Get set of all subfolders
    subfolders = set()
    for path in object_names_set:
        folder = "/".join(path.split("/")[:-1]) + "/"
        subfolders.add(folder)

    # Only the ones that are question_folders
    question_folders = [
        "/".join(name.split("/")[:-1]) + "/"
        for name in subfolders
        if name.split("/")[-2].startswith("question_part_")
    ]
    question_folders.sort()
    return question_folders


def get_consultation_folders() -> list[str]:
    """
    Get all consultation folder codes from S3.

    Returns:
        List of folder codes (e.g., ['healthcare-consultation', 'transport-consultation'])
    """
    try:
        s3 = _get_s3_resource()
        # Only include ExpectedBucketOwner if account_id is set (production environments)
        filter_params = {"Prefix": "app_data/consultations/"}
        if account_id:
            filter_params["ExpectedBucketOwner"] = account_id
        objects = s3.Bucket(settings.AWS_BUCKET_NAME).objects.filter(**filter_params)

        # Get unique consultation folders
        s3_codes = set()
        for obj in objects:
            if match := re.search(
                r"^app_data\/consultations\/([\w-]+)",
                str(obj.key),
            ):
                s3_codes.add(match.groups()[0])

        return list(s3_codes)
    except Exception:
        logger.exception("Failed to get S3 folders")
        return []
