import json
import re
from typing import Dict, List, Optional

from botocore.exceptions import ClientError
from django.conf import settings

from boto3_client import get_s3_client

logger = settings.LOGGER
account_id = settings.AWS_ACCOUNT_ID


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
    s3_client = get_s3_client()
    
    # List objects with the given prefix
    list_params = {"Bucket": bucket_name, "Prefix": inputs_path, "MaxKeys": 1000}
    if account_id:
        list_params["ExpectedBucketOwner"] = account_id
    
    response = s3_client.list_objects_v2(**list_params)
    objects = response.get("Contents", [])
    
    # Extract keys from S3 response
    object_names_set = {obj["Key"] for obj in objects}

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
    
    Scans the app_data/consultations/ prefix to find all consultation codes.

    Returns:
        List of folder codes (e.g., ['healthcare-consultation', 'transport-consultation'])
    """
    try:
        s3_client = get_s3_client()
        
        # List objects under app_data/consultations/ prefix
        list_params = {
            "Bucket": settings.AWS_BUCKET_NAME,
            "Prefix": "app_data/consultations/",
            "MaxKeys": 1000,
        }
        if account_id:
            list_params["ExpectedBucketOwner"] = account_id
        
        response = s3_client.list_objects_v2(**list_params)
        objects = response.get("Contents", [])

        # Get unique consultation folders
        # Extract the consultation code (first directory after app_data/consultations/)
        s3_codes = set()
        for obj in objects:
            key = obj["Key"]
            # Match consultation code: app_data/consultations/CODE/...
            if match := re.search(
                r"^app_data\/consultations\/([\w-]+)",
                str(key),
            ):
                s3_codes.add(match.groups()[0])

        return list(s3_codes)
    except Exception:
        logger.exception("Failed to get S3 folders")
        return []
