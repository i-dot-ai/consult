import argparse
import asyncio
import datetime
import json
import logging
import os
from pathlib import Path

import boto3
import pandas as pd
import sentry_sdk
import structlog
import urllib3
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat

from themefinder import (
    detail_detection,
    rule_2_themes_must_have_a_non_negligible_number_of_responses_slack,
    rule_4_themes_should_not_overlap_slack,
    theme_mapping,
)
from themefinder.llm import OpenAILLM

# The Fargate enricher reads ECS_CONTAINER_METADATA_URI_V4, which only exists on Fargate.
_execution_environment = (
    ExecutionEnvironmentType.FARGATE
    if os.environ.get("EXECUTION_CONTEXT") == "batch"
    else ExecutionEnvironmentType.LOCAL
)

logger = StructuredLogger(
    level="info",
    options={
        "execution_environment": _execution_environment,
        "log_format": LogOutputFormat.JSON,
        "ship_logs": True,
    },
)

# boto3/urllib3 log via stdlib `logging`, which StructuredLogger never configures.
# Route it through the same structlog JSON pipeline so it isn't silently dropped
# (root logger defaults to WARNING with no handler) or lost to stderr unformatted.
_stdlib_handler = logging.StreamHandler()
_stdlib_handler.setFormatter(
    structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("message"),
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )
)
logging.basicConfig(level=logging.INFO, handlers=[_stdlib_handler], force=True)

logger.set_context_field("batch_job_id", os.environ.get("AWS_BATCH_JOB_ID", "unknown"))
# Adopt the submitting Django request's context_id so both sides' logs join
# on a single field in OpenSearch. If CONTEXT_ID is absent (e.g. the script
# was invoked manually, outside a Batch submission), keep the context_id
# StructuredLogger generated automatically rather than overwriting it with
# a hardcoded "unknown".
incoming_context_id = os.environ.get("CONTEXT_ID")
if incoming_context_id:
    logger.set_context_field("context_id", incoming_context_id)

# Initialize Sentry if DSN is provided
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "unknown"),
        traces_sample_rate=1.0,
    )
    logger.info("Sentry initialized")


BUCKET_NAME = os.getenv("DATA_S3_BUCKET")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
BASE_PREFIX = "app_data/consultations/"

http = urllib3.PoolManager()


SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def download_s3_subdir(subdir: str) -> None:
    """
    Recursively downloads the contents of a specified subdirectory from S3
    to a local directory with the same name as the subdir.
    """
    prefix = str(Path(BASE_PREFIX) / subdir).rstrip("/") + "/"
    logger.info("prefix: {prefix}", prefix=prefix)
    logger.info("bucket: {bucket}", bucket=BUCKET_NAME)

    s3 = boto3.client("s3")

    paginator = s3.get_paginator("list_objects_v2")
    inputs_prefix = str(Path(BASE_PREFIX) / subdir / "inputs").rstrip("/") + "/"
    logger.info("S3 inputs prefix: {inputs_prefix}", inputs_prefix=inputs_prefix)
    pages = paginator.paginate(
        Bucket=BUCKET_NAME, Prefix=inputs_prefix, ExpectedBucketOwner=ACCOUNT_ID
    )
    logger.info(
        "Created paginator for bucket: {bucket} with prefix: {inputs_prefix}",
        bucket=BUCKET_NAME,
        inputs_prefix=inputs_prefix,
    )

    for page in pages:
        contents = page.get("Contents", [])
        for obj in contents:
            key = obj["Key"]
            if key.endswith((".csv", ".json", ".jsonl")):
                relative_path = os.path.relpath(key, prefix)
                local_path = Path(subdir) / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(
                    BUCKET_NAME,
                    key,
                    str(local_path),
                    ExtraArgs={"ExpectedBucketOwner": ACCOUNT_ID},
                )
                logger.info(
                    "Downloaded {key} to {local_path}",
                    key=key,
                    local_path=str(local_path),
                )


def upload_directory_to_s3(local_path: str) -> None:
    """
    Recursively uploads all files from a local directory to a corresponding subdir path in S3.

    Args:
        local_path (str): Local path to the directory to upload (e.g., outputs/mapping/2025_02_02).
    """
    s3 = boto3.client("s3")

    for root, _, files in os.walk(local_path):
        for file in files:
            local_file_path = Path(root) / file
            s3_key = str(Path(BASE_PREFIX) / local_file_path).replace("\\", "/")
            s3.upload_file(
                str(local_file_path),
                BUCKET_NAME,
                s3_key,
                ExtraArgs={"ExpectedBucketOwner": ACCOUNT_ID},
            )
            logger.info(
                "Uploaded {local_file_path} to s3://{bucket}/{s3_key}",
                local_file_path=str(local_file_path),
                bucket=BUCKET_NAME,
                s3_key=s3_key,
            )


def load_question(consultation_dir: str, question_dir: str) -> tuple:
    """
    Load question, response and theme data from specified directories.

    Args:
        consultation_dir: Base directory of the consultation
        question_dir: Directory containing question-specific data

    Returns:
        tuple: (question text, dataframe of responses, list of themes)
    """

    question_path = Path(consultation_dir) / "inputs" / question_dir / "question.json"
    responses_path = (
        Path(consultation_dir) / "inputs" / question_dir / "responses.jsonl"
    )
    themes_path = Path(consultation_dir) / "inputs" / question_dir / "themes.csv"

    with question_path.open() as f:
        question = json.load(f)["question_text"]

    # Read JSONL file line by line
    responses = []
    with responses_path.open() as f:
        for line in f:
            responses.append(json.loads(line))
    responses_df = pd.DataFrame(responses)
    responses = responses_df.rename(
        columns={"themefinder_id": "response_id", "text": "response"}
    )

    with themes_path.open() as f:
        themes = pd.read_csv(themes_path)
    themes["topic_id"] = [chr(65 + i) for i in range(len(themes))]
    themes["topic"] = themes["Theme Name"] + ": " + themes["Theme Description"]
    return question, responses, themes


async def process_consultation(consultation_dir: str, model_name: str) -> str:
    """
    Process all questions in a consultation directory, generating theme analyses.

    Creates a new directory structure for outputs:
    - consultation_dir/
      - outputs/
        - YYYY-MM-DD_HH-MM-SS/
          - question_dir_files

    Args:
        consultation_dir: Directory containing question subdirectories
        model_name: Language model instance for processing

    Returns:
        str: Path to the output directory
    """
    llm = OpenAILLM(
        model=model_name,
        request_kwargs={"temperature": 0},
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
    )

    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    skipped_questions = []
    for question_dir in os.listdir(Path(consultation_dir) / "inputs"):
        if "question" in question_dir:
            logger.set_context_field("question_id", question_dir)

            logger.info("Processing {question_id}...", question_id=question_dir)
            try:
                question_output_dir = (
                    Path(consultation_dir) / "outputs" / "mapping" / date / question_dir
                )
                if not question_output_dir.exists():
                    question_output_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(
                        "Created outputs directory at: {output_dir}",
                        output_dir=str(question_output_dir),
                    )

                question, responses_df, themes_df = load_question(
                    consultation_dir, question_dir
                )

                detail_df, _ = await detail_detection(
                    responses_df,
                    llm,
                    question=question,
                )
                detail_df = detail_df[["response_id", "evidence_rich"]]
                detail_df = detail_df.rename(columns={"response_id": "themefinder_id"})
                detail_df.to_json(
                    question_output_dir / "detail_detection.jsonl",
                    orient="records",
                    lines=True,
                )

                mapped_df, _ = await theme_mapping(
                    responses_df,
                    llm,
                    refined_themes_df=themes_df[["topic_id", "topic"]],
                    question=question,
                )
                mapped_df = mapped_df[["response_id", "labels"]]
                mapped_df = mapped_df.rename(
                    columns={"response_id": "themefinder_id", "labels": "theme_keys"}
                )
                mapped_df.to_json(
                    question_output_dir / "mapping.jsonl", orient="records", lines=True
                )

                themes_df = themes_df[["topic_id", "Theme Name", "Theme Description"]]
                themes_df.columns = ["theme_key", "theme_name", "theme_description"]
                themes_df.to_json(question_output_dir / "themes.json", orient="records")

                logger.info(
                    "Completed processing {question_id}, saved to {output_dir}",
                    question_id=question_dir,
                    output_dir=str(question_output_dir),
                )

                rule_2_messages, rule_2_failed = (
                    rule_2_themes_must_have_a_non_negligible_number_of_responses_slack(
                        mapped_df.to_dict(orient="records")
                    )
                )

                rule_3_messages, rule_3_failed = rule_4_themes_should_not_overlap_slack(
                    mapped_df.to_dict(orient="records")
                )

                msg = "failed ❌" if (rule_2_failed or rule_3_failed) else "passed ✅"

                message_title_block = {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"theme set mapping rules {msg} for {consultation_dir}/{question_dir}",
                    },
                }
                message = {
                    "text": f"theme set mapping rules {msg} for {consultation_dir}/{question_dir}",
                    "blocks": [message_title_block] + rule_2_messages + rule_3_messages,
                }
                response = http.request(
                    "POST",
                    SLACK_WEBHOOK_URL,
                    body=json.dumps(message),
                    headers={"Content-Type": "application/json"},
                )
                if response.status != 200:
                    response_data = (
                        response.data.decode("utf-8")
                        if response.data
                        else "No response data"
                    )
                    logger.error(
                        "Slack webhook failed with status {status}: {response_data}",
                        status=response.status,
                        response_data=response_data,
                    )
                else:
                    logger.info("Slack notification sent", slack_message=message)

            except Exception:
                logger.exception(
                    "Error processing {question_id}", question_id=question_dir
                )
                skipped_questions.append(question_dir)

    # Don't let the last question processed leak onto the summary line below.
    structlog.contextvars.unbind_contextvars("question_id")
    if skipped_questions:
        logger.warning(
            "Skipped questions: {skipped_questions}",
            skipped_questions=skipped_questions,
        )
    return str(Path(consultation_dir) / "outputs" / "mapping" / date)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a subdirectory from S3.")
    parser.add_argument(
        "--subdir",
        type=str,
        required=True,
        help="Subdirectory within the base S3 path to download.",
    )
    parser.add_argument(
        "--job-type",
        type=str,
        required=False,
        help="Type of job to execute.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    logger.set_context_field("consultation_code", args.subdir)

    logger.info("Starting processing for subdirectory: {subdir}", subdir=args.subdir)
    download_s3_subdir(args.subdir)
    output_dir = asyncio.run(process_consultation(args.subdir, args.model_name))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: {subdir}", subdir=args.subdir)
