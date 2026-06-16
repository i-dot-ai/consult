import json
import re
from typing import Dict, List, Optional

from botocore.exceptions import ClientError
from django.conf import settings

from consultations.utils import s3 as s3_utils

logger = settings.LOGGER
account_id = settings.AWS_ACCOUNT_ID


def read_jsonl(
    bucket_name: str, key: str, raise_if_missing: bool = True
) -> List[Dict]:
    """
    Read a JSONL file from S3 and return list of parsed objects.
    Args:
        bucket_name: S3 bucket name
        key: S3 key to JSONL file
        raise_if_missing: If False, return empty list instead of raising error
    Returns:
        List of parsed JSON objects (one per line)
    Raises:
        ClientError: If file doesn't exist and raise_if_missing=True
    """
    s3_client = s3_utils.get_s3_client()
    try:
        params = {
            "Bucket": bucket_name,
            "Key": key,
        }

        if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
            params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

        response = s3_client.get_object(**params)
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
    bucket_name: str, key: str, raise_if_missing: bool = True
) -> Optional[Dict]:
    """
    Read a JSON file from S3 and return parsed object.
    Args:
        bucket_name: S3 bucket name
        key: S3 key to JSON file
        raise_if_missing: If False, return None instead of raising error
    Returns:
        Parsed JSON object or None if not found and raise_if_missing=False
    Raises:
        ClientError: If file doesn't exist and raise_if_missing=True
    """
    s3_client = s3_utils.get_s3_client()
    try:
        params = {
            "Bucket": bucket_name,
            "Key": key,
        }
        if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
            params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

        response = s3_client.get_object(**params)
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
    s3 = s3_utils.get_s3_client()

    params = {
        "Bucket": bucket_name,
        "Prefix": inputs_path,
        "MaxKeys": 1000
    }

    if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
        params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

    response = s3.list_objects_v2(
        **params,
    )

    if 'Contents' not in response:
        return []

    object_names_set = {s3_object["Key"] for s3_object in response["Contents"]}
    subfolders = set()

    for path in object_names_set:
        folder = "/".join(path.split("/")[:-1]) + "/"
        subfolders.add(folder)

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
        s3 = s3_utils.get_s3_client()
        params = {
            "Bucket":settings.AWS_BUCKET_NAME,
            "MaxKeys":200,
            "Prefix":'app_data/consultations/',
        }

        if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
            params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

        response = s3.list_objects_v2(
            **params,
        )

        if 'Contents' not in response:
            return []

        s3_keys = [s3_object["Key"] for s3_object in response["Contents"]]
        s3_codes = set()
        pattern = r'app_data/consultations/([^/]+)/.+'
        for obj in s3_keys:
            if match := re.search(
                pattern,
                obj,
            ):
                s3_codes.add(match.groups()[0])
        return list(s3_codes)
    except Exception:
        logger.exception("Failed to get S3 folders")
        return []
