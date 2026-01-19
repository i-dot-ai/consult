import json
import re
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = settings.LOGGER


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
        s3_client = boto3.client("s3")

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        if not raise_if_missing and e.response["Error"]["Code"] == "NoSuchKey":
            logger.info(f"File not found (skipping): {key}")
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
        s3_client = boto3.client("s3")

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        data = json.loads(response["Body"].read())
        return data
    except ClientError as e:
        if not raise_if_missing and e.response["Error"]["Code"] == "NoSuchKey":
            logger.info(f"File not found (skipping): {key}")
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
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=inputs_path)
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
        s3 = boto3.resource("s3")
        objects = s3.Bucket(settings.AWS_BUCKET_NAME).objects.filter(
            Prefix="app_data/consultations/"
        )

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
