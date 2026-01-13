import argparse
import asyncio
import datetime
import json
import logging
import os
from pathlib import Path

import boto3
import pandas as pd
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from themefinder import theme_condensation, theme_generation, theme_mapping, theme_refinement
from themefinder.models import HierarchicalClusteringResponse
from themefinder.theme_clustering_agent import ThemeClusteringAgent, ThemeNode


class ThemeNodeList(BaseModel):
    """List of theme nodes for serialization to JSON."""

    theme_nodes: list[ThemeNode]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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


async def generate_themes(question: str, responses_df):
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


def prepare_long_list(refined_themes_df):
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
    df, save_path: str, question: str, n_responses: int, short_list: bool = False
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
            format_to_use = highlight_format if short_list and col_num < 4 else wrap_format
            for row_num in range(len(df)):
                worksheet.write(row_num + 3, col_num, df.iloc[row_num, col_num], format_to_use)

            # Set column width based on content
            max_length = max(df[col].astype(str).apply(len).max(), len(str(col)))
            worksheet.set_column(col_num, col_num, min(max_length + 2, 50))


def produce_short_list_df(themes_df, mapped_df):
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
    topic_counts: dict[str, int] = {}
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
    short_list.reset_index(inplace=True)
    return short_list.sort_values(by="Count", ascending=False)


def agentic_theme_selection(
    refined_themes_df,
    llm,
    min_selected_themes=10,
    max_selected_themes=20,
    max_cluster_iterations=0,
    n_target_themes=10,
):
    """
    Iteratively select themes using clustering with adaptive significance threshold.
    Will retry a fixed number of times before defaulting to top 20 themes.

    Parameters:
    -----------
    refined_themes_df : pd.DataFrame
        DataFrame containing themes with 'topic' column
    llm : object
        Language model object for theme clustering
    min_selected_themes : int, default=10
        Minimum number of themes to select
    max_selected_themes : int, default=20
        Maximum number of themes to select
    max_cluster_iterations : int, default=0
        Maximum number of clustering iterations to attempt
    n_target_themes : int, default=10
        Number of themes to target

    Returns:
    --------
    pd.DataFrame
        Selected themes with 'Theme Name', 'Theme Description', and 'topic' columns
    """
    refined_themes_df[["topic_label", "topic_description"]] = refined_themes_df["topic"].str.split(
        ":", n=1, expand=True
    )
    selected_themes = pd.DataFrame()

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
        llm.with_structured_output(HierarchicalClusteringResponse),
        initial_themes,
    )
    logger.info(
        f"Clustering themes with max_iterations={max_cluster_iterations}, target_themes={n_target_themes}"
    )
    for i in range(3):
        try:
            all_themes_df = agent.cluster_themes(
                max_iterations=max_cluster_iterations, target_themes=n_target_themes
            )
            if len(all_themes_df) > 0:
                break
        except:  # noqa: E722
            logger.info(f"Error when clustering, attempt {i}, retrying")

    selected_themes = pd.DataFrame()
    significance_percentage = 1
    while (
        len(selected_themes) < min_selected_themes or len(selected_themes) > max_selected_themes
    ) and (significance_percentage < 20):
        selected_themes = agent.select_themes(significance_percentage)
        significance_percentage += 1
    selected_themes["topic"] = (
        selected_themes["topic_label"] + ": " + selected_themes["topic_description"]
    )

    return selected_themes, all_themes_df


async def process_consultation(consultation_dir: str, llm) -> str:
    """
    Process all questions in a consultation directory, generating theme analyses.

    Creates a new directory structure for outputs:
    - consultation_dir/
      - outputs/
        - YYYY-MM-DD_HH-MM-SS/
          - question_dir_files

    Args:
        consultation_dir: Directory containing question subdirectories
        llm: Language model instance for processing
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

                # Select short list, using clustering if more than 20 themes
                if len(refined_themes_df) > 20:
                    selected_themes, _all_themes_df = agentic_theme_selection(
                        refined_themes_df, llm
                    )
                    all_themes_list = [ThemeNode(**row) for _, row in _all_themes_df.iterrows()]

                    selected_themes["Theme Name"] = selected_themes["topic_label"]
                    selected_themes["Theme Description"] = selected_themes["topic_description"]
                else:
                    logger.info("Fewer than 20 themes, clustering not required")
                    selected_themes = refined_themes_df.copy()

                    def refined_themes_to_theme_node(row: dict):
                        topic_label, topic_description = row["topic"].split(":")
                        return ThemeNode(
                            topic_id=row["topic_id"],
                            topic_label=topic_label,
                            topic_description=topic_description,
                            source_topic_count=row["source_topic_count"],
                            parent_id="0",
                            children=[],
                        )

                    all_themes_list = [
                        refined_themes_to_theme_node(row) for _, row in refined_themes_df.iterrows()
                    ]

                with open(os.path.join(question_output_dir, "clustered_themes.json"), "w") as f:
                    f.write(ThemeNodeList(theme_nodes=all_themes_list).model_dump_json())

                pd.DataFrame(all_themes_list).to_json(
                    os.path.join(question_output_dir, "clustered_themes.json"), orient="records"
                )

                # Map responses to themes, including "None of the above" option
                mapping_themes = selected_themes[["topic_id", "topic"]].copy()
                mapping_themes = pd.concat(
                    [
                        mapping_themes,
                        pd.DataFrame(
                            [
                                {
                                    "topic_id": "XYZ",
                                    "topic": "None of the above: the response doesn't match any of the provided topics.",
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

                mapped_df, _ = await theme_mapping(
                    responses_df,
                    llm,
                    refined_themes_df=mapping_themes[["topic_id", "topic"]],
                    question=question,
                )
                logger.info("N unprocessables: %d", len(_))

                # Save detailed short list
                short_list_path = question_output_dir / "detailed_short_list.xlsx"
                save_to_excel(
                    produce_short_list_df(selected_themes, mapped_df),
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
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        openai_api_base=os.environ["LLM_GATEWAY_URL"],
        openai_api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
    )

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
    output_dir = asyncio.run(process_consultation(args.subdir, llm))
    upload_directory_to_s3(output_dir)
    logger.info("Processing completed for subdirectory: %s", args.subdir)
