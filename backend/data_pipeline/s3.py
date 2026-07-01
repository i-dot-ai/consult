import json
from typing import Dict, List, Optional

from botocore.exceptions import BotoCoreError, ClientError
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
        logger.exception("Error reading JSONL from S3: {key}", key=key)
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
        logger.exception("Error reading JSON from S3: {key}", key=key)
        raise


def get_question_folders(inputs_path: str, bucket_name: str) -> List[str]:
    """
    Get all question_part_N folders from the inputs path.

    Uses list_objects_v2 with Delimiter to efficiently list only subdirectories
    without iterating through individual files. Paginates through all results.

    Args:
        inputs_path: S3 path to inputs folder (e.g., "app_data/consultations/CODE/inputs/")
        bucket_name: S3 bucket name
    Returns:
        Sorted list of question folder paths ending with /

    Raises:
        ClientError | BotoCoreError: If S3 cannot be reached or the request fails.
    """
    s3 = s3_utils.get_s3_client()

    params = {
        "Bucket": bucket_name,
        "Prefix": inputs_path,
        "Delimiter": "/",  # Group by directory to get only subdirectories
        "MaxKeys": 1000,   # Max allowed per page by AWS
    }

    if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
        params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

    question_folders: List[str] = []
    continuation_token = None
    page_count = 0

    logger.info(
        "Starting S3 listing for question folders: bucket={bucket}, prefix={prefix}",
        bucket=bucket_name,
        prefix=inputs_path,
    )

    # Paginate through all results
    while True:
        page_count += 1
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        try:
            response = s3.list_objects_v2(**params)
        except (ClientError, BotoCoreError):
            logger.exception(
                "list_objects_v2 failed on page {page} (bucket={bucket}, prefix={prefix}, "
                "{count} question folders found across {pages} prior page(s))",
                page=page_count,
                bucket=bucket_name,
                prefix=inputs_path,
                count=len(question_folders),
                pages=page_count - 1,
            )
            raise

        # Process directory prefixes (CommonPrefixes contains directories)
        if "CommonPrefixes" in response:
            prefixes_in_page = [p["Prefix"] for p in response["CommonPrefixes"]]
            logger.info(
                "Page {page}: Found {count} directories: {prefixes}",
                page=page_count,
                count=len(prefixes_in_page),
                prefixes=prefixes_in_page,
            )

            for prefix_info in response["CommonPrefixes"]:
                prefix = prefix_info["Prefix"]
                # Check if this is a question_part_N folder
                folder_name = prefix.rstrip("/").split("/")[-1]
                if folder_name.startswith("question_part_"):
                    question_folders.append(prefix)
        else:
            logger.info("Page {page}: No CommonPrefixes found", page=page_count)

        # Check if more pages exist
        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            logger.info("More pages available, continuing pagination...")
        else:
            logger.info("Pagination complete after {pages} page(s)", pages=page_count)
            break

    question_folders.sort()
    logger.info(
        "Found {count} question folders total: {folders}",
        count=len(question_folders),
        folders=question_folders,
    )
    return question_folders


def get_consultation_folders() -> list[str]:
    """
    Get all consultation folder codes from S3.

    Uses list_objects_v2 with Delimiter to efficiently list only directory-level
    prefixes without iterating through individual files. Paginates through all results.

    Returns:
        Sorted list of consultation codes (e.g., ['co_digital_id', 'healthcare-consultation']).
        Returns an empty list if no consultation folders exist yet - this is a valid state,
        not an error.

    Raises:
        ClientError | BotoCoreError: If S3 cannot be reached or the request fails.
    """
    s3 = s3_utils.get_s3_client()
    params = {
        "Bucket": settings.AWS_BUCKET_NAME,
        "Prefix": "app_data/consultations/",
        "Delimiter": "/",  # Group by directory to get only top-level consultation folders
        "MaxKeys": 1000,   # Max allowed per page by AWS
    }

    if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
        params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID

    s3_codes = set()
    continuation_token = None
    page_count = 0
    total_prefixes_processed = 0

    logger.info(
        "Starting S3 listing for consultation folders: bucket={bucket}, prefix={prefix}",
        bucket=settings.AWS_BUCKET_NAME,
        prefix="app_data/consultations/",
    )

    # Paginate through all results
    while True:
        page_count += 1
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        try:
            response = s3.list_objects_v2(**params)
        except (ClientError, BotoCoreError):
            logger.exception(
                "list_objects_v2 failed on page {page} (bucket={bucket}, prefix={prefix}, "
                "processed {total} prefixes across {pages} prior page(s))",
                page=page_count,
                bucket=settings.AWS_BUCKET_NAME,
                prefix="app_data/consultations/",
                total=total_prefixes_processed,
                pages=page_count - 1,
            )
            raise

        # Process directory prefixes (CommonPrefixes contains directories)
        if "CommonPrefixes" in response:
            prefixes_in_page = []
            codes_in_page = []

            for prefix_info in response["CommonPrefixes"]:
                prefix = prefix_info["Prefix"]
                prefixes_in_page.append(prefix)
                # Extract consultation code: app_data/consultations/CODE/ -> CODE
                code = prefix.rstrip("/").split("/")[-1]
                s3_codes.add(code)
                codes_in_page.append(code)
                total_prefixes_processed += 1

            logger.info(
                "Page {page}: Found {count} consultation directories",
                page=page_count,
                count=len(prefixes_in_page),
            )
            logger.info(
                "Page {page} prefixes: {prefixes}",
                page=page_count,
                prefixes=prefixes_in_page,
            )
            logger.info(
                "Page {page} codes extracted: {codes}",
                page=page_count,
                codes=codes_in_page,
            )
        else:
            logger.info("Page {page}: No CommonPrefixes found", page=page_count)

        # Log files if any (shouldn't be any at this level, but good to know)
        if "Contents" in response:
            file_count = len(response["Contents"])
            logger.info(
                "Page {page}: Also found {count} files at consultation root level",
                page=page_count,
                count=file_count,
            )

        # Check if more pages exist
        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken")
            logger.info(
                "Page {page}: More results available, continuing pagination (processed {total} prefixes so far)...",
                page=page_count,
                total=total_prefixes_processed,
            )
        else:
            logger.info(
                "Pagination complete after {pages} page(s), processed {total} total prefixes",
                pages=page_count,
                total=total_prefixes_processed,
            )
            break

    sorted_codes = sorted(list(s3_codes))
    logger.info(
        "Final result: Found {count} unique consultation codes: {codes}",
        count=len(sorted_codes),
        codes=sorted_codes,
    )
    return sorted_codes
