import argparse
import asyncio
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import boto3
import pandas as pd
from django.conf import settings
from langchain_openai import ChatOpenAI
from themefinder import (
    theme_condensation,
    theme_generation,
    theme_mapping,
    theme_refinement,
)

logger = settings.LOGGER


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_base=os.environ["LLM_GATEWAY_URL"],
    openai_api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
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
        local_path (str): Local path to the directory to upload (e.g., outputs/sign_off/2025_02_02).
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
    Load question and response data from specified directories.

    Args:
        consultation_dir: Base directory of the consultation
        question_dir: Directory containing question-specific data

    Returns:
        tuple: (question text, dataframe of responses)
    """
    question_path = Path(consultation_dir) / "inputs" / question_dir / "question.json"
    responses_path = Path(consultation_dir) / "inputs" / question_dir / "responses.jsonl"

    with question_path.open() as f:
        question = json.load(f)["question_text"]

    # Read JSONL file line by line
    responses = []
    with responses_path.open() as f:
        for line in f:
            responses.append(json.loads(line))
    responses_df = pd.DataFrame(responses)
    responses = responses_df.rename(columns={"themefinder_id": "response_id", "text": "response"})
    return question, responses


async def generate_themes(question: str, responses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate refined themes from question and responses through multiple analysis steps.

    Args:
        question: The survey question text
        responses_df: DataFrame containing survey responses

    Returns:
        pd.DataFrame: DataFrame containing refined themes
    """
    theme_df, _ = await theme_generation(responses_df, llm, question=question, partition_key=None)

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


def prepare_long_list(refined_themes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a sorted long list of themes with names, descriptions, and frequencies.

    Args:
        refined_themes_df: DataFrame containing refined themes

    Returns:
        pd.DataFrame: Formatted long list of themes sorted by frequency
    """
    refined_themes_df["Theme Name"] = refined_themes_df["topic"].str.split(":").str[0]
    refined_themes_df["Theme Description"] = refined_themes_df["topic"].str.split(":").str[1]

    long_list = refined_themes_df[["Theme Name", "Theme Description", "source_topic_count"]]
    long_list.columns = ["Theme Name", "Theme Description", "Approximate Frequency"]

    return long_list.sort_values(by="Approximate Frequency", ascending=False)


def save_to_excel(
    df: pd.DataFrame, save_path: str, question: str, n_responses: int, short_list: bool = False
) -> None:
    """
    Save theme list (long or short) to Excel with formatted columns and cells.

    Args:
        df: DataFrame containing theme analysis results
        save_path: Path where Excel file should be saved
        question: The survey question to display as title
        n_responses: Total number of responses for this question
        short_list: If True, highlights first 3 columns differently
    """
    with pd.ExcelWriter(save_path, engine="xlsxwriter") as writer:
        # Write DataFrame starting from row 2 to leave space for title
        df.to_excel(writer, index=False, startrow=2)

        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Define formats
        title_format = workbook.add_format(
            {"bold": True, "font_size": 14, "text_wrap": True, "align": "left", "valign": "vcenter"}
        )

        header_format = workbook.add_format({"bold": True, "bg_color": "#D9D9D9", "border": 1})

        wrap_format = workbook.add_format({"text_wrap": True, "border": 1})

        highlight_format = workbook.add_format(
            {
                "text_wrap": True,
                "border": 1,
                "bg_color": "#E6F3FF",  # Light blue background
            }
        )

        # Write title in first row and merge cells
        worksheet.merge_range(
            0,
            0,
            1,
            len(df.columns) - 1,
            question + "  " + f" Number Responses: {n_responses}",
            title_format,
        )
        worksheet.set_row(0, 40)  # Set height of title row

        # Apply formats and adjust column widths
        for col_num, col in enumerate(df.columns):
            # Write header (now in row 2 due to title)
            worksheet.write(2, col_num, col, header_format)

            # Write data cells with appropriate format
            format_to_use = highlight_format if short_list and col_num < 3 else wrap_format
            for row_num in range(len(df)):
                worksheet.write(row_num + 3, col_num, df.iloc[row_num, col_num], format_to_use)

            # Set column width based on content
            max_length = max(df[col].astype(str).apply(len).max(), len(str(col)))
            worksheet.set_column(col_num, col_num, min(max_length + 2, 50))


def produce_short_list_df(themes_df: pd.DataFrame, mapped_df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a detailed short list of themes with examples from responses.

    Args:
        themes_df: DataFrame containing theme information
        mapped_df: DataFrame with responses mapped to themes

    Returns:
        pd.DataFrame: Short list of themes with examples, sorted by count
    """
    # Create a copy of the themes DataFrame with topic_id as index
    short_list = themes_df.copy()
    short_list.set_index("topic_id", inplace=True)
    short_list = short_list[["Theme Name", "Theme Description"]]

    # Count occurrences of each topic in the mapped responses
    topic_counts: Dict[Any, Any] = {}
    for labels in mapped_df["labels"]:
        for topic_id in labels:
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1

    # Add count column to the short list
    short_list["Count"] = short_list.index.map(lambda x: topic_counts.get(x, 0))

    # Add example responses for each theme (up to 10)
    for topic_id in short_list.index:
        matching_rows = mapped_df[mapped_df["labels"].apply(lambda x: topic_id in x)]
        examples = matching_rows["response"].head(10).tolist()
        examples.extend(
            [""] * (10 - len(examples))
        )  # Pad with empty strings if fewer than 10 examples

        for i, example in enumerate(examples, 1):
            short_list.loc[topic_id, f"Example {i}"] = example

    # Sort by count in descending order
    return short_list.sort_values(by="Count", ascending=False)


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
    """
    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    skipped_questions = []
    for question_dir in os.listdir(Path(consultation_dir) / "inputs"):
        if "question" in question_dir:
            logger.info("Processing %s...", question_dir)
            try:
                # Create question-specific directory in the datestamped folder
                question_output_dir = (
                    Path(consultation_dir) / "outputs" / "sign_off" / date / question_dir
                )
                if not question_output_dir.exists():
                    question_output_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Created outputs directory at: %s", question_output_dir)

                # Load question and responses
                question, responses_df = load_question(consultation_dir, question_dir)

                # Generate themes
                refined_themes_df = await generate_themes(question, responses_df)

                # Save long list of themes
                long_list_path = question_output_dir / "theme_long_list.xlsx"
                save_to_excel(
                    prepare_long_list(refined_themes_df),
                    str(long_list_path),
                    question=question,
                    n_responses=len(responses_df),
                )

                # Select top 20 themes for short list
                top_themes_df = refined_themes_df.iloc[:20]
                # Map responses to themes

                mapped_df, _ = await theme_mapping(
                    responses_df,
                    llm,
                    refined_themes_df=top_themes_df[["topic_id", "topic"]],
                    question=question,
                )
                logger.info("N unprocessables: %d", len(_))

                # Save detailed short list
                short_list_path = question_output_dir / "detailed_short_list.xlsx"
                save_to_excel(
                    produce_short_list_df(top_themes_df, mapped_df),
                    str(short_list_path),
                    question=question,
                    short_list=True,
                    n_responses=len(responses_df),
                )

                logger.info(
                    "Completed processing %s, saved to %s", question_dir, question_output_dir
                )
            except Exception:
                logger.exception("Error processing %s", question_dir)
                skipped_questions.append(question_dir)
    if skipped_questions:
        logger.warning("Skipped questions: %s", skipped_questions)
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
    args = parser.parse_args()

    logger.info("Starting processing for subdirectory: %s", args.subdir)
    download_s3_subdir(args.subdir)
    output_dir = asyncio.run(process_consultation(args.subdir))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: %s", args.subdir)
