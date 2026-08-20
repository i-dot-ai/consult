"""Data acquisition for theme mapping evaluation.

Fetches theme-mapping evaluation datasets either from Langfuse (preferred)
or from the local on-disk fallback (see `datasets.load_local_data`), and
normalises both sources into a common item shape that `evaluate.py` can
consume without needing to know where the data came from.
"""

import json
import sys
from datetime import date
from pathlib import Path

# Add the evals/ directory to the path so sibling modules (langfuse_utils,
# datasets) can be imported when this script is run directly from within
# pipelines/mapping/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import langfuse_utils
import pandas as pd
from datasets import DatasetConfig, load_local_data


def _normalise_langfuse_item(item) -> dict:
    """Convert a Langfuse dataset item into the common item shape.

    Args:
        item: Langfuse dataset item (has .input, .expected_output,
            .metadata, .id)

    Returns:
        Dict with question_part, responses_df, question, topics_df,
        expected_output, and the original Langfuse item (kept so callers
        can still create trace-linked runs via `langfuse_utils.dataset_item_trace`).
    """
    responses_df = pd.DataFrame(item.input["responses"])
    question = item.input["question"]
    topics_df = pd.DataFrame(item.input["topics"])
    topics_df = topics_df.rename(columns={"topic_id": "topic_id", "topic": "topic"})

    return {
        "question_part": item.metadata.get("question_part", item.id),
        "responses_df": responses_df,
        "question": question,
        "topics_df": topics_df,
        "expected_output": item.expected_output,
        "langfuse_item": item,
    }


def _normalise_local_item(item: dict) -> dict:
    """Convert a local dataset item dict into the common item shape.

    Args:
        item: Dict as returned by `datasets.load_local_data`

    Returns:
        Dict with question_part, responses_df, question, topics_df,
        expected_output, and `langfuse_item` set to None.
    """
    responses_df = pd.DataFrame(item["input"]["responses"])
    question = item["input"]["question"]
    topics_df = pd.DataFrame(item["input"]["topics"])

    return {
        "question_part": item.get("metadata", {}).get("question_part", "unknown"),
        "responses_df": responses_df,
        "question": question,
        "topics_df": topics_df,
        "expected_output": item["expected_output"],
        "langfuse_item": None,
    }


def fetch_langfuse_dataset_items(
    ctx: langfuse_utils.LangfuseContext, config: DatasetConfig
) -> list[dict] | None:
    """Fetch and normalise dataset items from Langfuse.

    Args:
        ctx: LangfuseContext with an active client
        config: DatasetConfig identifying the dataset to fetch

    Returns:
        List of normalised items, or None if the dataset could not be
        retrieved from Langfuse (callers should fall back to local data).
    """
    try:
        dataset = ctx.client.get_dataset(config.name)
    except Exception as e:
        print(
            f"Dataset {config.name} not found in Langfuse, falling back to local: {e}"
        )
        return None

    return [_normalise_langfuse_item(item) for item in dataset.items]


def load_local_dataset_items(
    config: DatasetConfig, question_num: int | None = None
) -> list[dict]:
    """Load and normalise dataset items from the local fallback data.

    Args:
        config: DatasetConfig identifying the dataset to load
        question_num: Optional specific question number (1-3) to filter to

    Returns:
        List of normalised items
    """
    data_items = load_local_data(config)

    if question_num is not None:
        data_items = [
            item
            for item in data_items
            if f"part_{question_num}"
            in item.get("metadata", {}).get("question_part", "")
        ]

    return [_normalise_local_item(item) for item in data_items]


def get_dataset_items(
    ctx: langfuse_utils.LangfuseContext,
    config: DatasetConfig,
    question_num: int | None = None,
) -> list[dict]:
    """Get normalised mapping-eval dataset items, preferring Langfuse.

    Args:
        ctx: LangfuseContext (may or may not be enabled)
        config: DatasetConfig identifying the dataset to load
        question_num: Optional specific question number (1-3). Only applied
            to the local fallback - Langfuse datasets are used in full.

    Returns:
        List of normalised items, each with keys: question_part,
        responses_df, question, topics_df, expected_output, langfuse_item
        (None for locally-sourced items).
    """
    if ctx.is_enabled:
        items = fetch_langfuse_dataset_items(ctx, config)
        if items is not None:
            return items

    return load_local_dataset_items(config, question_num)


def write_dataset_items_to_local(config: DatasetConfig, items: list[dict]) -> Path:
    """Persist normalised dataset items to `evals/data/<dataset>/`.

    Writes each question part in the same layout expected by
    `datasets.load_local_data` (`inputs/<question_part>/{question.json,
    responses.jsonl}` and `outputs/mapping/<date>/<question_part>/
    {themes.json, mapping.jsonl}`), so the dataset - regardless of whether it
    was originally fetched from Langfuse or local disk - is always available
    as a local, version-controllable fallback under
    `config.local_path` (a subdirectory of `evals/data/` named after the
    dataset).

    Args:
        config: DatasetConfig identifying the dataset (its `local_path` is
            `evals/data/<dataset>`)
        items: Normalised dataset items, as returned by `get_dataset_items`

    Returns:
        The directory the dataset was written to (`config.local_path`)
    """
    output_dir = config.local_path
    date_str = date.today().isoformat()

    for item in items:
        question_part = item["question_part"]

        inputs_dir = output_dir / "inputs" / question_part
        inputs_dir.mkdir(parents=True, exist_ok=True)

        with open(inputs_dir / "question.json", "w") as f:
            json.dump({"question_text": item["question"]}, f, indent=4)

        with open(inputs_dir / "responses.jsonl", "w") as f:
            for _, row in item["responses_df"][["response_id", "response"]].iterrows():
                f.write(
                    json.dumps(
                        {
                            "response_id": row["response_id"],
                            "response": row["response"],
                        }
                    )
                    + "\n"
                )

        outputs_dir = output_dir / "outputs" / "mapping" / date_str / question_part
        outputs_dir.mkdir(parents=True, exist_ok=True)

        with open(outputs_dir / "themes.json", "w") as f:
            json.dump(item["topics_df"].to_dict(orient="records"), f, indent=4)

        mappings = item["expected_output"].get("mappings", {})
        with open(outputs_dir / "mapping.jsonl", "w") as f:
            for response_id, labels in mappings.items():
                f.write(
                    json.dumps({"response_id": response_id, "labels": labels}) + "\n"
                )

    return output_dir


if __name__ == "__main__":
    import argparse

    import dotenv

    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(
        description="Download/inspect theme mapping evaluation data"
    )
    parser.add_argument(
        "--dataset",
        default="gambling_XS",
        help="Dataset identifier (e.g., gambling_XS)",
    )
    parser.add_argument(
        "--question", type=int, default=None, help="Specific question number (1-3)"
    )
    args = parser.parse_args()

    dataset_config = DatasetConfig(dataset=args.dataset, stage="mapping")
    langfuse_ctx = langfuse_utils.get_langfuse_context(
        session_id="download_data_check",
        eval_type="mapping",
        metadata={"dataset": args.dataset},
        tags=[args.dataset],
    )

    dataset_items = get_dataset_items(langfuse_ctx, dataset_config, args.question)
    source = (
        "Langfuse" if dataset_items and dataset_items[0]["langfuse_item"] else "local"
    )
    print(
        f"Loaded {len(dataset_items)} item(s) for dataset '{args.dataset}' from {source} source"
    )
    for dataset_item in dataset_items:
        print(
            f"  {dataset_item['question_part']}: "
            f"{len(dataset_item['responses_df'])} responses, "
            f"{len(dataset_item['topics_df'])} topics"
        )

    written_dir = write_dataset_items_to_local(dataset_config, dataset_items)
    print(f"Wrote dataset to {written_dir}")
