import argparse
import asyncio
import collections
import datetime
import json
import logging
import os
from pathlib import Path

import boto3
import pandas as pd
import urllib3
from langchain_openai import ChatOpenAI
from themefinder import detail_detection, theme_mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BUCKET_NAME = os.getenv("DATA_S3_BUCKET")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
BASE_PREFIX = "app_data/consultations/"

http = urllib3.PoolManager()


SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def rule_2_themes_must_have_a_non_negligible_number_of_responses(
    mapping: list[dict],
) -> list[tuple[str, int, int]]:
    """
    A child theme must be assigned to at least 0.1% or 5, whichever is the greater, of the responses
    Rationale: We want to remove anomalous results from the consultation.
    """

    counter = collections.defaultdict(int)

    for line in mapping:
        for theme_key in line["theme_keys"]:
            counter[theme_key] += 1

    return [
        (theme_key, count, len(mapping))
        for theme_key, count in counter.items()
        if count / len(mapping) >= 0.001 or count > 5
    ]


def rule_4_themes_should_not_overlap(mapping: list[dict]) -> list[tuple[str, str, float]]:
    """
    The size of intersection of any two themes representative responses divined by the size of the union of its representative responses should be less than 70%
    Rationale: We do not want 2 themes, even if semantically distinct, to be mapped to the same response-set, in this case they can be merged.
    """
    counter = collections.defaultdict(set)

    for line in mapping:
        for theme_key in line["theme_keys"]:
            counter[theme_key].add(line["themefinder_id"])

    theme_keys = list(counter)

    results = []
    for i, theme_key_a in enumerate(theme_keys):
        for theme_key_b in enumerate(theme_keys[i + 1 :]):
            response_a, response_b = theme_keys[theme_key_a], theme_keys[theme_key_b]
            intersection = len(set.intersection(response_a, response_b))
            union = len(set.union(response_a, response_b))
            if intersection / union > 0.7:
                results.append((theme_key_a, theme_key_b, intersection / union))
    return results


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
    pages = paginator.paginate(
        Bucket=BUCKET_NAME, Prefix=inputs_prefix, ExpectedBucketOwner=ACCOUNT_ID
    )
    logger.info("Created paginator for bucket: %s with prefix: %s", BUCKET_NAME, inputs_prefix)

    for page in pages:
        contents = page.get("Contents", [])
        for obj in contents:
            key = obj["Key"]
            if key.endswith((".csv", ".json", ".jsonl")):
                relative_path = os.path.relpath(key, prefix)
                local_path = Path(subdir) / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(
                    BUCKET_NAME, key, str(local_path), ExtraArgs={"ExpectedBucketOwner": ACCOUNT_ID}
                )
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
            s3.upload_file(
                str(local_file_path),
                BUCKET_NAME,
                s3_key,
                ExtraArgs={"ExpectedBucketOwner": ACCOUNT_ID},
            )
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
    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_base=os.environ["LLM_GATEWAY_URL"],
        openai_api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
    )

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

                detail_df, _ = await detail_detection(
                    responses_df,
                    llm,
                    question=question,
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
                    "Completed processing %s, saved to %s", question_dir, question_output_dir
                )

                message_blocks = []
                passed = True
                if sparse_responses := rule_2_themes_must_have_a_non_negligible_number_of_responses(
                    themes_df.to_dict(orient="records")
                ):
                    passed = False
                    message_blocks.extend(
                        [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "Rule 2 failed\n*expected:* all responses to be mapped to at least 0.1% of responses\n*actual:* the following themes are too sparse",
                                },
                            },
                            {
                                "type": "rich_text",
                                "elements": [
                                    {  # type: ignore
                                        "type": "rich_text_list",
                                        "style": "bullet",
                                        "elements": [
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": f"`{theme}` is mapped to {coverage} responses",
                                                    }
                                                ],
                                            }
                                            for theme, coverage, _ in sparse_responses
                                        ],
                                    }
                                ],
                            },
                        ]
                    )
                else:
                    message_blocks.append(
                        {"type": "section", "text": {"type": "mrkdwn", "text": "Rule 2 passed"}}
                    )

                if overlapping_themes := rule_4_themes_should_not_overlap(
                    themes_df.to_dict(orient="records")
                ):
                    # str, str, float
                    passed = False
                    message_blocks.extend(
                        [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "Rule 4 failed\n*expected:* no themes should have mapped responses that overlap by more than 70%%\n*actual:* the following themes overlap",
                                },
                            },
                            {
                                "type": "rich_text",
                                "elements": [
                                    {  # type: ignore
                                        "type": "rich_text_list",
                                        "style": "bullet",
                                        "elements": [
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": f"`{theme_a}` & `{theme_b}` overlap by {overlap}",
                                                    }
                                                ],
                                            }
                                            for theme_a, theme_b, overlap in overlapping_themes
                                        ],
                                    }
                                ],
                            },
                        ]
                    )
                else:
                    message_blocks.append(
                        {"type": "section", "text": {"type": "mrkdwn", "text": "Rule 4 passed"}}
                    )

                if passed:
                    message_title = (
                        f"theme set rules passed ✅ for {consultation_dir}/{question_dir}"
                    )
                else:
                    message_title = (
                        f"theme set rules failed ❌ for {consultation_dir}/{question_dir}"
                    )

                message_title_block = {
                    "type": "header",
                    "text": {"type": "plain_text", "text": message_title},
                }
                message = {
                    "text": message_title,
                    "blocks": [message_title_block] + message_blocks,
                }
                response = http.request(
                    "POST",
                    SLACK_WEBHOOK_URL,
                    body=json.dumps(message),
                    headers={"Content-Type": "application/json"},
                )
                if response.status != 200:
                    response_data = (
                        response.data.decode("utf-8") if response.data else "No response data"
                    )
                    error_message = (
                        f"Slack webhook failed with status {response.status}: {response_data}"
                    )
                    logger.error(error_message)

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
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    logger.info("Starting processing for subdirectory: %s", args.subdir)
    download_s3_subdir(args.subdir)
    output_dir = asyncio.run(process_consultation(args.subdir, args.model_name))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: %s", args.subdir)
