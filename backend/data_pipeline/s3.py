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
    
    Uses FileStore which automatically prefixes paths with IAI_FS_DATA_DIR (app_data/consultations).

    Args:
        inputs_path: S3 path to inputs folder (e.g., "app_data/consultations/CODE/inputs/")
        bucket_name: S3 bucket name (unused, kept for API compatibility)

    Returns:
        Sorted list of question folder paths ending with /
    """
    from boto3_client import _get_file_store
    
    file_store = _get_file_store()
    
    # Convert absolute path to relative path for FileStore
    # inputs_path is like "app_data/consultations/CODE/inputs/"
    # We need to make it relative to IAI_FS_DATA_DIR: "CODE/inputs/"
    relative_path = inputs_path.replace("app_data/consultations/", "")
    
    # List objects with the relative path - FileStore will prepend IAI_FS_DATA_DIR
    objects = file_store.list_objects(prefix=relative_path, max_keys=1000)
    
    # Extract keys from the list of object dictionaries
    object_names_set = {obj["key"] for obj in objects}

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
    
    Uses FileStore which automatically prefixes paths with IAI_FS_DATA_DIR (app_data/consultations).
    Lists objects from the root of the data directory to find consultation codes.

    Returns:
        List of folder codes (e.g., ['healthcare-consultation', 'transport-consultation'])
    """
    try:
        from boto3_client import _get_file_store
        
        file_store = _get_file_store()
        # List from root of IAI_FS_DATA_DIR (app_data/consultations/)
        # FileStore will automatically prepend IAI_FS_DATA_DIR to the prefix
        objects = file_store.list_objects(prefix="", max_keys=1000)

        # Get unique consultation folders
        # Keys returned by FileStore include the full path: app_data/consultations/CODE/...
        # Extract the consultation code (first directory after the data_dir prefix)
        s3_codes = set()
        for obj in objects:
            key = obj["key"]
            # Match consultation code at the start of the relative path
            # After IAI_FS_DATA_DIR prefix is applied, paths look like: app_data/consultations/CODE/...
            if match := re.search(
                r"^app_data\/consultations\/([\w-]+)",
                str(key),
            ):
                s3_codes.add(match.groups()[0])

        return list(s3_codes)
    except Exception:
        logger.exception("Failed to get S3 folders")
        return []
