"""Theme mapping response generation and evaluation.

Runs the theme mapping task (assigning themes to responses) against
evaluation data - fetched via `download_data.py` - and scores the results,
with Langfuse dataset/experiment support when configured.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import dotenv

# Add the evals/ directory to the path so sibling modules (langfuse_utils,
# utils_gateway, datasets, evaluators, metrics) can be imported when this
# script is run directly from within pipelines/mapping/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import langfuse_utils
import utils_gateway
from datasets import DatasetConfig
from download_data import get_dataset_items
from evaluators import mapping_f1_evaluator
from metrics import calculate_mapping_metrics
from themefinder.llm import OpenAILLM

from themefinder import theme_mapping


async def evaluate_mapping(
    dataset: str = "gambling_XS",
    question_num: int | None = None,
    llm: OpenAILLM | None = None,
    langfuse_ctx: langfuse_utils.LangfuseContext | None = None,
) -> dict:
    """Run mapping evaluation.

    Args:
        dataset: Dataset identifier (e.g., "gambling_S", "healthcare_M")
        question_num: Optional specific question number (1-3) to evaluate
        llm: Optional pre-configured LLM instance (for benchmark runs)
        langfuse_ctx: Optional pre-configured Langfuse context (for benchmark runs)

    Returns:
        Dict containing evaluation scores
    """
    dotenv.load_dotenv()

    config = DatasetConfig(dataset=dataset, stage="mapping")

    # Use provided context or create new one
    owns_context = langfuse_ctx is None
    if langfuse_ctx is None:
        session_id = f"{config.name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        langfuse_ctx = langfuse_utils.get_langfuse_context(
            session_id=session_id,
            eval_type="mapping",
            metadata={"dataset": dataset},
            tags=[dataset],
        )

    # Use provided LLM or create new one
    if llm is None:
        base_url, api_key = utils_gateway.gateway_credentials()
        llm = OpenAILLM(
            model=os.getenv("AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT"),
            request_kwargs={"temperature": 0},
            base_url=base_url,
            api_key=api_key,
        )

    # Fetch data - download_data.py handles the Langfuse vs local branching
    # and normalises both sources into a common item shape.
    dataset_items = get_dataset_items(langfuse_ctx, config, question_num)

    if langfuse_ctx.is_enabled and dataset_items and dataset_items[0]["langfuse_item"]:
        result = await _run_with_langfuse(langfuse_ctx, dataset_items, llm)
    else:
        result = await _run_local_fallback(dataset_items, llm)

    # Only flush if we created the context
    if owns_context:
        langfuse_utils.flush(langfuse_ctx)
    return result


async def _run_with_langfuse(ctx, dataset_items: list[dict], llm) -> dict:
    """Run evaluation with manual dataset iteration for proper trace control.

    Args:
        ctx: LangfuseContext
        dataset_items: Normalised dataset items (see `download_data.py`),
            each carrying its original Langfuse item under "langfuse_item"
        llm: LangChain LLM instance

    Returns:
        Dict containing evaluation scores
    """
    all_scores = {}

    for item in dataset_items:
        langfuse_item = item["langfuse_item"]

        # Create trace for this item with full metadata
        with langfuse_utils.dataset_item_trace(ctx, langfuse_item, ctx.session_id) as (
            trace,
            trace_id,
        ):
            # Run theme mapping
            result_df, unprocessable_df = await theme_mapping(
                responses_df=item["responses_df"][["response_id", "response"]],
                llm=llm,
                question=item["question"],
                refined_themes_df=item["topics_df"],
            )
            if not unprocessable_df.empty:
                print(
                    f"  Warning: {len(unprocessable_df)} responses could not be processed"
                )

            # Build labels map
            labels = dict(
                zip(
                    result_df["response_id"].astype(str),
                    result_df["labels"].tolist(),
                )
            )
            output = {"labels": labels}

            # Update trace with output
            if trace:
                trace.update(output=output)

            # Run evaluator and attach score
            eval_result = mapping_f1_evaluator(
                output=output,
                expected_output=item["expected_output"],
            )

            if trace_id and ctx.client:
                ctx.client.create_score(
                    trace_id=trace_id,
                    name=eval_result.name,
                    value=eval_result.value,
                    data_type="NUMERIC",
                )

            # Collect for return
            item_key = item["question_part"]
            all_scores[f"{item_key}_f1"] = eval_result.value

            # Include pipeline output for disk persistence
            all_scores[f"{item_key}_output"] = output

    print(f"Mapping Eval Results: {ctx.session_id}")
    return all_scores


async def _run_local_fallback(dataset_items: list[dict], llm) -> dict:
    """Run evaluation without Langfuse (local development).

    Args:
        dataset_items: Normalised dataset items (see `download_data.py`)
        llm: LangChain LLM instance

    Returns:
        Dict containing evaluation scores
    """
    all_scores = {}

    for item in dataset_items:
        question_part = item["question_part"]
        responses_df = item["responses_df"]
        expected_mappings = item["expected_output"]["mappings"]

        result, unprocessable_df = await theme_mapping(
            responses_df=responses_df[["response_id", "response"]],
            llm=llm,
            question=item["question"],
            refined_themes_df=item["topics_df"][["topic_id", "topic"]],
        )
        if not unprocessable_df.empty:
            print(
                f"  Warning: {len(unprocessable_df)} responses could not be processed"
            )

        # Merge for comparison
        responses_df["topics"] = (
            responses_df["response_id"].astype(str).map(expected_mappings)
        )
        responses_df = responses_df.merge(
            result[["response_id", "labels"]], "inner", on="response_id"
        )

        mapping_metrics = calculate_mapping_metrics(
            df=responses_df, column_one="topics", column_two="labels"
        )
        print(f"Theme Mapping ({question_part}): \n {mapping_metrics}")

        # Collect scores with question prefix
        for key, value in mapping_metrics.items():
            if isinstance(value, (int, float)):
                all_scores[f"{question_part}_{key}"] = value

    return all_scores


def write_results(results: dict, output_path: Path) -> None:
    """Persist evaluation results to a JSON file for DVC to track as a metric.

    Args:
        results: Dict of evaluation scores (as returned by `evaluate_mapping`)
        output_path: Path to write the JSON results to
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    import nest_asyncio

    nest_asyncio.apply()

    parser = argparse.ArgumentParser(description="Run theme mapping evaluation")
    parser.add_argument(
        "--dataset",
        default="gambling_XS",
        help="Dataset identifier (e.g., gambling_XS)",
    )
    parser.add_argument(
        "--question", type=int, default=None, help="Specific question number (1-3)"
    )
    parser.add_argument(
        "--output",
        default="scores.json",
        help="Path to write evaluation results (JSON)",
    )
    args = parser.parse_args()

    scores = asyncio.run(
        evaluate_mapping(dataset=args.dataset, question_num=args.question)
    )
    write_results(scores, Path(args.output))
