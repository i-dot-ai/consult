import asyncio
import datetime
import json
import os
import tempfile
from pathlib import Path

import boto3
import pandas as pd
import structlog
import urllib3
from django.conf import settings
from openai import OpenAI
from pydantic import BaseModel
from themefinder.tasks import theme_condensation, theme_generation, theme_refinement
from themefinder.themeset_rules import (
    rule_1_total_theme_number_less_than_70_slack,
    rule_3_semantic_similarity_must_be_less_than_90pc_slack,
)
from themefinder.advanced_tasks.theme_clustering_agent import ThemeClusteringAgent
from themefinder.llm import OpenAILLM
from themefinder.models import ThemeNode

logger = settings.LOGGER
http = urllib3.PoolManager()

BASE_PREFIX = "app_data/consultations"


class ThemeNodeList(BaseModel):
    theme_nodes: list[ThemeNode]


def download_consultation_inputs(consultation_code: str, destination: Path) -> None:
    """Download the existing ThemeFinder S3 input contract into a temporary directory."""
    prefix = f"{BASE_PREFIX}/{consultation_code}/inputs/"
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=settings.AWS_BUCKET_NAME,
        Prefix=prefix,
        ExpectedBucketOwner=settings.AWS_ACCOUNT_ID,
    )

    for page in pages:
        for item in page.get("Contents", []):
            key = item["Key"]
            if not key.endswith((".csv", ".json", ".jsonl")):
                continue
            relative_path = Path(key).relative_to(f"{BASE_PREFIX}/{consultation_code}")
            local_path = destination / relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(
                settings.AWS_BUCKET_NAME,
                key,
                str(local_path),
                ExtraArgs={"ExpectedBucketOwner": settings.AWS_ACCOUNT_ID},
            )


def upload_find_themes_outputs(
    consultation_code: str, run_date: str, output_directory: Path
) -> None:
    """Upload generated files without exposing the worker's temporary local path in S3."""
    s3 = boto3.client("s3")
    for local_path in output_directory.rglob("*"):
        if not local_path.is_file():
            continue
        relative_path = local_path.relative_to(output_directory)
        key = f"{BASE_PREFIX}/{consultation_code}/outputs/sign_off/{run_date}/{relative_path}"
        with local_path.open("rb") as output_file:
            s3.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=key,
                Body=output_file,
                ExpectedBucketOwner=settings.AWS_ACCOUNT_ID,
            )


def load_question(
    consultation_directory: Path, question_directory: str
) -> tuple[str, pd.DataFrame]:
    question_path = consultation_directory / "inputs" / question_directory / "question.json"
    responses_path = consultation_directory / "inputs" / question_directory / "responses.jsonl"

    with question_path.open() as question_file:
        question = json.load(question_file)["question_text"]

    with responses_path.open() as responses_file:
        responses = [json.loads(line) for line in responses_file]

    responses_df = pd.DataFrame(responses).rename(
        columns={"themefinder_id": "response_id", "text": "response"}
    )
    return question, responses_df


async def generate_themes(question: str, responses_df: pd.DataFrame, llm) -> pd.DataFrame:
    generated, _ = await theme_generation(responses_df, llm, question=question, partition_key=None)
    condensed, _ = await theme_condensation(generated, llm, question=question)
    refined, _ = await theme_refinement(condensed, llm, question=question)
    return refined


async def cluster_themes(
    refined_themes_df: pd.DataFrame,
    llm,
    max_cluster_iterations: int = 0,
    target_themes: int = 10,
) -> pd.DataFrame | None:
    refined_themes_df[["topic_label", "topic_description"]] = refined_themes_df["topic"].str.split(
        ":", n=1, expand=True
    )
    initial_themes = [
        ThemeNode(
            topic_id=row["topic_id"],
            topic_label=row["topic_label"],
            topic_description=row["topic_description"],
            source_topic_count=row["source_topic_count"],
        )
        for _, row in refined_themes_df.iterrows()
    ]
    agent = ThemeClusteringAgent(llm, initial_themes, target_themes=target_themes)

    for attempt in range(3):
        try:
            themes = await agent.cluster_themes(
                max_iterations=max_cluster_iterations, target_themes=target_themes
            )
            if len(themes) > 0:
                return themes
        except Exception:
            logger.exception("Theme clustering failed on attempt {attempt}", attempt=attempt + 1)

    logger.warning("Theme clustering failed after 3 attempts; using unclustered themes")
    return None


def _refined_theme_to_node(row) -> ThemeNode:
    topic_label, topic_description = row["topic"].split(":", 1)
    return ThemeNode(
        topic_id=row["topic_id"],
        topic_label=topic_label,
        topic_description=topic_description,
        source_topic_count=row["source_topic_count"],
        parent_id="0",
        children=[],
    )


def _send_quality_notification(
    consultation_code: str, question_directory: str, themes: list[ThemeNode]
) -> None:
    """Preserve the existing ThemeFinder quality notification sent for each question."""
    client = OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
    )
    rule_1_messages, rule_1_failed = rule_1_total_theme_number_less_than_70_slack(themes)
    rule_3_messages, rule_3_failed = rule_3_semantic_similarity_must_be_less_than_90pc_slack(
        themes, client
    )
    result = "failed" if rule_1_failed or rule_3_failed else "passed"
    title = f"theme set discovery rules {result} for {consultation_code}/{question_directory}"
    message = {
        "text": title,
        "blocks": [{"type": "header", "text": {"type": "plain_text", "text": title}}]
        + rule_1_messages
        + rule_3_messages,
    }
    webhook_url = os.environ.get("THEMEFINDER_SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("ThemeFinder Slack webhook is not configured; skipping quality notification")
        return
    response = http.request(
        "POST",
        webhook_url,
        body=json.dumps(message),
        headers={"Content-Type": "application/json"},
    )
    if response.status != 200:
        logger.error(
            "ThemeFinder Slack notification failed with status {status}", status=response.status
        )


async def process_consultation(
    consultation_directory: Path, consultation_code: str, model_name: str, run_date: str
) -> Path:
    llm = OpenAILLM(
        model=model_name,
        request_kwargs={"temperature": 0},
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
    )
    output_directory = consultation_directory / "outputs" / "sign_off" / run_date
    skipped_questions: list[str] = []

    for question_path in sorted((consultation_directory / "inputs").iterdir()):
        if not question_path.is_dir() or "question" not in question_path.name:
            continue
        with structlog.contextvars.bound_contextvars(question_id=question_path.name):
            responses_path = question_path / "responses.jsonl"
            if not responses_path.exists():
                logger.info(
                    "Skipping closed question {question_id}", question_id=question_path.name
                )
                continue
            try:
                question, responses_df = load_question(consultation_directory, question_path.name)
                refined = await generate_themes(question, responses_df, llm)
                themes: list[ThemeNode]
                if len(refined) > 20:
                    clustered = await cluster_themes(refined, llm)
                    themes = (
                        [ThemeNode(**row) for _, row in clustered.iterrows()]
                        if clustered is not None
                        else [_refined_theme_to_node(row) for _, row in refined.iterrows()]
                    )
                else:
                    themes = [_refined_theme_to_node(row) for _, row in refined.iterrows()]

                question_output = output_directory / question_path.name
                question_output.mkdir(parents=True, exist_ok=True)
                (question_output / "clustered_themes.json").write_text(
                    ThemeNodeList(theme_nodes=themes).model_dump_json()
                )
                _send_quality_notification(consultation_code, question_path.name, themes)
            except Exception:
                logger.exception(
                    "Failed to find themes for {question_id}", question_id=question_path.name
                )
                skipped_questions.append(question_path.name)

    if skipped_questions:
        raise RuntimeError(f"Failed to find themes for questions: {', '.join(skipped_questions)}")
    return output_directory


def find_themes(consultation_code: str, model_name: str) -> str:
    """Run the former Batch script inside the worker and return its S3 run date."""
    # A unique run prefix prevents retries from importing stale files from an earlier run.
    run_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S-%f")
    with tempfile.TemporaryDirectory(prefix=f"find-themes-{consultation_code}-") as temporary:
        consultation_directory = Path(temporary) / consultation_code
        download_consultation_inputs(consultation_code, consultation_directory)
        output_directory = asyncio.run(
            process_consultation(consultation_directory, consultation_code, model_name, run_date)
        )
        upload_find_themes_outputs(consultation_code, run_date, output_directory)
    return run_date
