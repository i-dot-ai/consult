import argparse
import asyncio
import datetime
import json
import logging
import os
from pathlib import Path

import boto3
import pandas as pd
from langchain_openai import AzureChatOpenAI
from themefinder import detail_detection, sentiment_analysis, theme_mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

llm = AzureChatOpenAI(
    model="gpt-4o",
    temperature=0,
)
BUCKET_NAME = os.getenv("DATA_S3_BUCKET")
BASE_PREFIX = "app_data/consultations/"


def download_s3_subdir(subdir: str) -> None:
    """
    Recursively downloads the contents of a specified subdirectory from S3
    to a local directory with the same name as the subdir.
    """
    prefix = str(Path(BASE_PREFIX) / subdir).rstrip("/") + "/"
    logger.info("prefix: %s", prefix)
    logger.info("bucket: %s", BUCKET_NAME)

    s3 = boto3.client("s3")

    paginator = s3.get_paginator("list_objects_v2")
    inputs_prefix = str(Path(BASE_PREFIX) / subdir / "inputs").rstrip("/") + "/"
    logger.info("S3 inputs prefix: %s", inputs_prefix)
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=inputs_prefix)
    logger.info("Created paginator for bucket: %s with prefix: %s", BUCKET_NAME, inputs_prefix)

    for page in pages:
        contents = page.get("Contents", [])
        for obj in contents:
            key = obj["Key"]
            if key.endswith((".csv", ".json", ".jsonl")):
                relative_path = os.path.relpath(key, prefix)
                local_path = Path(subdir) / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(BUCKET_NAME, key, str(local_path))
                logger.info("Downloaded %s to %s", key, local_path)


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
            s3.upload_file(str(local_file_path), BUCKET_NAME, s3_key)
            logger.info("Uploaded %s to s3://%s/%s", local_file_path, BUCKET_NAME, s3_key)


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
    responses_path = Path(consultation_dir) / "inputs" / question_dir / "responses.jsonl"
    themes_path = Path(consultation_dir) / "inputs" / question_dir / "themes.csv"

    with question_path.open() as f:
        question = json.load(f)["question_text"]

    # Read JSONL file line by line
    responses = []
    with responses_path.open() as f:
        for line in f:
            responses.append(json.loads(line))
    responses_df = pd.DataFrame(responses)
    responses = responses_df.rename(columns={"themefinder_id": "response_id", "text": "response"})

    with themes_path.open() as f:
        themes = pd.read_csv(themes_path)
    themes["topic_id"] = [chr(65 + i) for i in range(len(themes))]
    themes["topic"] = themes["Theme Name"] + ": " + themes["Theme Description"]
    return question, responses, themes


async def process_consultation(consultation_dir: str = "test_consultation") -> str:
    """
    Process all questions in a consultation directory, generating theme analyses.

    Creates a new directory structure for outputs:
    - consultation_dir/
      - outputs/
        - YYYY-MM-DD_HH-MM-SS/
          - question_dir_files

    Args:
        consultation_dir: Directory containing question subdirectories

    Returns:
        str: Path to the output directory
    """
    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    skipped_questions = []
    for question_dir in os.listdir(Path(consultation_dir) / "inputs"):
        if "question" in question_dir:
            logger.info("Processing %s...", question_dir)
            try:
                question_output_dir = (
                    Path(consultation_dir) / "outputs" / "mapping" / date / question_dir
                )
                if not question_output_dir.exists():
                    question_output_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Created outputs directory at: %s", question_output_dir)

                question, responses_df, themes_df = load_question(consultation_dir, question_dir)
                sentiment_df, _ = await sentiment_analysis(
                    responses_df,
                    llm,
                    question=question,
                    concurrency=1,
                )
                sentiment_df = sentiment_df[["response_id", "position"]]
                sentiment_df = sentiment_df.rename(
                    columns={"response_id": "themefinder_id", "position": "sentiment"}
                )
                sentiment_df.to_json(
                    question_output_dir / "sentiment.jsonl", orient="records", lines=True
                )

                detail_df, _ = await detail_detection(
                    responses_df,
                    llm,
                    question=question,
                    concurrency=1,
                )
                detail_df = detail_df[["response_id", "evidence_rich"]]
                detail_df = detail_df.rename(columns={"response_id": "themefinder_id"})
                detail_df.to_json(
                    question_output_dir / "detail_detection.jsonl", orient="records", lines=True
                )

                mapped_df, _ = await theme_mapping(
                    responses_df,
                    llm,
                    refined_themes_df=themes_df[["topic_id", "topic"]],
                    question=question,
                    concurrency=1,
                )
                mapped_df = mapped_df[["response_id", "labels", "stances"]]
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
                    "Completed processing %s, saved to %s", question_dir, question_output_dir
                )
            except Exception:
                logger.exception("Error processing %s", question_dir)
                skipped_questions.append(question_dir)
    if skipped_questions:
        logger.warning("Skipped questions: %s", skipped_questions)
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
    args = parser.parse_args()

    logger.info("Starting processing for subdirectory: %s", args.subdir)
    download_s3_subdir(args.subdir)
    output_dir = asyncio.run(process_consultation(args.subdir))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: %s", args.subdir)
