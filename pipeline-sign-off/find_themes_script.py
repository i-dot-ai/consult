import argparse
import asyncio
import datetime
import json
import os
from pathlib import Path

import boto3
import pandas as pd
import structlog
import urllib3
from openai import OpenAI
from pipeline_common import bootstrap_logger
from pydantic import BaseModel

from themefinder import (
    rule_1_total_theme_number_less_than_70_slack,
    rule_3_semantic_similarity_must_be_less_than_90pc_slack,
    theme_condensation,
    theme_generation,
    theme_refinement,
)
from themefinder.advanced_tasks.theme_clustering_agent import ThemeClusteringAgent
from themefinder.llm import OpenAILLM
from themefinder.models import (
    ThemeNode,
)

http = urllib3.PoolManager()

client = OpenAI(
    base_url=os.environ["LLM_GATEWAY_URL"],
    api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
)


SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


class ThemeNodeList(BaseModel):
    """List of theme nodes for serialization to JSON."""

    theme_nodes: list[ThemeNode]


logger = bootstrap_logger()


BUCKET_NAME = os.getenv("DATA_S3_BUCKET")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
BASE_PREFIX = "app_data/consultations/"


def download_s3_subdir(subdir: str) -> None:
    """
    Recursively downloads the contents of a specified subdirectory from S3
    to a local directory with the same name as the subdir.
    """
    prefix = str(Path(BASE_PREFIX) / subdir).rstrip("/") + "/"
    logger.info("prefix: {prefix}; bucket: {bucket}", prefix=prefix, bucket=BUCKET_NAME)

    s3 = boto3.client("s3")

    paginator = s3.get_paginator("list_objects_v2")
    inputs_prefix = str(Path(BASE_PREFIX) / subdir / "inputs").rstrip("/") + "/"
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
        local_path (str): Local path to the directory to upload (e.g., outputs/sign_off/2025_02_02).
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
    Load question and response data from specified directories.

    Args:
        consultation_dir: Base directory of the consultation
        question_dir: Directory containing question-specific data

    Returns:
        tuple: (question text, dataframe of responses)
    """
    question_path = Path(consultation_dir) / "inputs" / question_dir / "question.json"
    responses_path = (
        Path(consultation_dir) / "inputs" / question_dir / "responses.jsonl"
    )

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
    return question, responses


async def generate_themes(question: str, responses_df, llm):
    """
    Generate refined themes from question and responses through multiple analysis steps.

    Args:
        question: The survey question text
        responses_df: DataFrame containing survey responses
        llm: the model to use

    Returns:
        pd.DataFrame: DataFrame containing refined themes
    """
    theme_df, _ = await theme_generation(
        responses_df, llm, question=question, partition_key=None
    )

    condensed_theme_df, _ = await theme_condensation(
        theme_df,
        llm,
        question=question,
    )
    refined_themes_df, _ = await theme_refinement(
        condensed_theme_df,
        llm,
        question=question,
    )

    return refined_themes_df


async def agentic_theme_clustering(
    refined_themes_df,
    llm,
    max_cluster_iterations=0,
    n_target_themes=10,
):
    """
    Cluster themes using hierarchical clustering.

    Parameters:
    -----------
    refined_themes_df : pd.DataFrame
        DataFrame containing themes with 'topic' column
    llm : object
        Language model object for theme clustering
    max_cluster_iterations : int, default=0
        Maximum number of clustering iterations to attempt
    n_target_themes : int, default=10
        Number of themes to target

    Returns:
    --------
    pd.DataFrame
        All themes from clustering
    """
    refined_themes_df[["topic_label", "topic_description"]] = refined_themes_df[
        "topic"
    ].str.split(":", n=1, expand=True)

    initial_themes = [
        ThemeNode(
            topic_id=row["topic_id"],
            topic_label=row["topic_label"],
            topic_description=row["topic_description"],
            source_topic_count=row["source_topic_count"],
        )
        for _, row in refined_themes_df.iterrows()
    ]
    agent = ThemeClusteringAgent(
        llm,
        initial_themes,
        target_themes=n_target_themes,
    )
    logger.info(
        "Clustering themes with max_iterations={max_iterations}, target_themes={target_themes}",
        max_iterations=max_cluster_iterations,
        target_themes=n_target_themes,
    )
    all_themes_df = None
    for i in range(3):
        try:
            all_themes_df = await agent.cluster_themes(
                max_iterations=max_cluster_iterations, target_themes=n_target_themes
            )
            if len(all_themes_df) > 0:
                break
        except Exception:
            logger.exception(
                "Error when clustering, attempt {attempt}, retrying", attempt=i
            )

    if all_themes_df is None or len(all_themes_df) == 0:
        logger.warning("Theme clustering failed after 3 attempts")
        return None

    return all_themes_df


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
            with structlog.contextvars.bound_contextvars(question_id=question_dir):
                # Closed / multiple-choice questions have no free-text responses.jsonl to
                # find themes in — skip them quietly rather than raising a FileNotFoundError.
                responses_path = (
                    Path(consultation_dir) / "inputs" / question_dir / "responses.jsonl"
                )
                if not responses_path.exists():
                    logger.info(
                        "Skipping {question_id}: no free-text responses (closed question)",
                        question_id=question_dir,
                    )
                    continue

                logger.info("Processing {question_id}...", question_id=question_dir)
                try:
                    # Create question-specific directory in the datestamped folder
                    question_output_dir = (
                        Path(consultation_dir)
                        / "outputs"
                        / "sign_off"
                        / date
                        / question_dir
                    )
                    if not question_output_dir.exists():
                        question_output_dir.mkdir(parents=True, exist_ok=True)
                        logger.info(
                            "Created outputs directory at: {output_dir}",
                            output_dir=str(question_output_dir),
                        )

                    # Load question and responses
                    question, responses_df = load_question(
                        consultation_dir, question_dir
                    )

                    # Generate themes
                    refined_themes_df = await generate_themes(
                        question, responses_df, llm
                    )

                    def refined_themes_to_theme_node(row: dict):
                        topic_label, topic_description = row["topic"].split(":", 1)
                        return ThemeNode(
                            topic_id=row["topic_id"],
                            topic_label=topic_label,
                            topic_description=topic_description,
                            source_topic_count=row["source_topic_count"],
                            parent_id="0",
                            children=[],
                        )

                    # Cluster themes if more than 20
                    if len(refined_themes_df) > 20:
                        all_themes_df = await agentic_theme_clustering(
                            refined_themes_df, llm
                        )
                        if all_themes_df is not None:
                            all_themes_list = [
                                ThemeNode(**row) for _, row in all_themes_df.iterrows()
                            ]
                        else:
                            logger.info("Clustering failed, using unclustered themes")
                            all_themes_list = [
                                refined_themes_to_theme_node(row)
                                for _, row in refined_themes_df.iterrows()
                            ]
                    else:
                        logger.info("Fewer than 20 themes, clustering not required")
                        all_themes_list = [
                            refined_themes_to_theme_node(row)
                            for _, row in refined_themes_df.iterrows()
                        ]

                    rule_1_messages, rule_1_failed = (
                        rule_1_total_theme_number_less_than_70_slack(all_themes_list)
                    )

                    rule_3_messages, rule_3_failed = (
                        rule_3_semantic_similarity_must_be_less_than_90pc_slack(
                            all_themes_list, client
                        )
                    )

                    msg = (
                        "failed ❌" if (rule_1_failed or rule_3_failed) else "passed ✅"
                    )

                    message_title_block = {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"theme set discovery rules {msg} for {consultation_dir}/{question_dir}",
                        },
                    }
                    message = {
                        "text": f"theme set discovery rules {msg} for {consultation_dir}/{question_dir}",
                        "blocks": [message_title_block]
                        + rule_1_messages
                        + rule_3_messages,
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

                    with open(
                        os.path.join(question_output_dir, "clustered_themes.json"), "w"
                    ) as f:
                        f.write(
                            ThemeNodeList(theme_nodes=all_themes_list).model_dump_json()
                        )

                    logger.info(
                        "Completed processing {question_id}, saved to {output_dir}",
                        question_id=question_dir,
                        output_dir=str(question_output_dir),
                    )
                except Exception:
                    logger.exception(
                        "Error processing {question_id}", question_id=question_dir
                    )
                    skipped_questions.append(question_dir)
    if skipped_questions:
        logger.warning(
            "Skipped questions: {skipped_questions}",
            skipped_questions=skipped_questions,
        )
    return str(Path(consultation_dir) / "outputs" / "sign_off" / date)


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
    parser.add_argument(
        "--context-id",
        type=str,
        required=False,
        help="context_id from the submitting Django request, for log correlation.",
    )
    args = parser.parse_args()

    logger.set_context_field("consultation_code", args.subdir)
    if args.context_id:
        logger.set_context_field("context_id", args.context_id)

    # Log sentry initialization after context set
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        logger.info("Sentry initialized")

    logger.info("Starting processing for subdirectory: {subdir}", subdir=args.subdir)
    download_s3_subdir(args.subdir)
    output_dir = asyncio.run(process_consultation(args.subdir, args.model_name))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: {subdir}", subdir=args.subdir)
