"""Theme generation evaluation with Langfuse dataset and experiment support.

Evaluates the full theme generation pipeline (generation -> condensation -> refinement)
against a ground truth theme framework.
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime

import dotenv
import pandas as pd
import utils_gateway
from datasets import DatasetConfig, load_local_data
from evaluators import (
    create_coverage_evaluator,
    create_groundedness_evaluator,
    create_redundancy_evaluator,
    create_title_specificity_evaluator,
)
from themefinder.llm import OpenAILLM
from utils import langfuse_utils

from themefinder import theme_condensation, theme_generation, theme_refinement

logger = logging.getLogger("themefinder.evals.generation")


def _build_output(refined_df: pd.DataFrame) -> dict:
    """Split combined "label: description" topic field into separate fields
    for evaluators that need the label alone (specificity, redundancy)."""
    themes = []
    for record in refined_df.to_dict(orient="records"):
        if "topic" in record and ":" in record["topic"]:
            label, description = record["topic"].split(":", 1)
            record["topic_label"] = label.strip()
            record["topic_description"] = description.strip()
        themes.append(record)
    return {"themes": themes}


async def evaluate_generation(
    dataset: str = "gambling_XS",
    llm: OpenAILLM | None = None,
    langfuse_ctx: langfuse_utils.LangfuseContext | None = None,
    judge_llm: OpenAILLM | None = None,
) -> dict:
    """Run generation evaluation.

    Args:
        dataset: Dataset identifier (e.g., "gambling_S", "healthcare_M")
        llm: Optional pre-configured LLM instance (for benchmark runs)
        langfuse_ctx: Optional pre-configured Langfuse context (for benchmark runs)

    Returns:
        Dict containing evaluation scores
    """
    dotenv.load_dotenv()

    config = DatasetConfig(dataset=dataset, stage="generation")

    # Use provided context or create new one
    owns_context = langfuse_ctx is None
    if langfuse_ctx is None:
        session_id = f"{config.name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        langfuse_ctx = langfuse_utils.get_langfuse_context(
            session_id=session_id,
            eval_type="generation",
            metadata={"dataset": dataset},
            tags=[dataset],
        )

    # Use provided LLM or create new one
    if llm is None:
        base_url, api_key = utils_gateway.gateway_credentials()
        llm = OpenAILLM(
            model=os.getenv("AUTO_EVAL_MODEL"),
            request_kwargs={"temperature": 0},
            base_url=base_url,
            api_key=api_key,
        )

    # Branch: Langfuse dataset vs local fallback
    if langfuse_ctx.is_enabled:
        result = await _run_with_langfuse(
            langfuse_ctx, config, llm, judge_llm=judge_llm
        )
    else:
        result = await _run_local_fallback(config, llm, judge_llm=judge_llm)

    # Only flush if we created the context
    if owns_context:
        langfuse_utils.flush(langfuse_ctx)
    return result


async def _run_with_langfuse(ctx, config: DatasetConfig, llm, judge_llm=None) -> dict:
    """Run evaluation with manual dataset iteration for proper trace control.

    Args:
        ctx: LangfuseContext
        config: DatasetConfig
        llm: LLM instance
        judge_llm: Optional dedicated judge LLM (defaults to task llm)

    Returns:
        Dict containing evaluation scores
    """
    try:
        dataset = ctx.client.get_dataset(config.name)
    except Exception as e:
        print(
            f"Dataset {config.name} not found in Langfuse, falling back to local: {e}"
        )
        return await _run_local_fallback(config, llm, judge_llm=judge_llm)

    # Use dedicated judge LLM if provided, otherwise fall back to task LLM
    eval_llm = judge_llm or llm

    # Create evaluator functions
    groundedness_evaluator = create_groundedness_evaluator(eval_llm)
    coverage_evaluator = create_coverage_evaluator(eval_llm)
    specificity_evaluator = create_title_specificity_evaluator(eval_llm)
    redundancy_evaluator = create_redundancy_evaluator()

    all_scores = {}
    items = list(dataset.items)

    for item in items:
        # Create trace for this item with full metadata
        with langfuse_utils.dataset_item_trace(ctx, item, ctx.session_id) as (
            trace,
            trace_id,
        ):
            # Extract input
            responses_df = pd.DataFrame(item.input["responses"])
            question = item.input["question"]

            # Run full pipeline
            themes_df, _ = await theme_generation(
                responses_df=responses_df,
                llm=llm,
                question=question,
            )
            condensed_df, _ = await theme_condensation(
                themes_df,
                llm=llm,
                question=question,
            )
            refined_df, _ = await theme_refinement(
                condensed_df,
                llm=llm,
                question=question,
            )

            output = _build_output(refined_df)

            # Update trace with output
            if trace:
                trace.update(output=output)

            llm_results = await asyncio.gather(
                groundedness_evaluator(
                    output=output, expected_output=item.expected_output
                ),
                coverage_evaluator(output=output, expected_output=item.expected_output),
                specificity_evaluator(
                    output=output, expected_output=item.expected_output
                ),
                return_exceptions=True,
            )

            # Run redundancy evaluator synchronously (embedding-based, no LLM call)
            redundancy_result = redundancy_evaluator(
                output=output, expected_output=item.expected_output
            )

            # Process all results
            all_eval_results = list(llm_results) + [redundancy_result]
            item_key = item.metadata.get("question_part", item.id)
            for eval_result in all_eval_results:
                if isinstance(eval_result, Exception):
                    logger.error(f"Evaluator failed: {eval_result}")
                    continue

                if trace_id and ctx.client:
                    # Extract name, value, comment from either Evaluation object or dict
                    if isinstance(eval_result, dict):
                        eval_name = eval_result.get("name", "unknown")
                        eval_value = eval_result.get("value", 0.0)
                        eval_comment = eval_result.get("comment")
                    else:
                        eval_name = eval_result.name
                        eval_value = eval_result.value
                        eval_comment = getattr(eval_result, "comment", None)

                    score_kwargs = {
                        "trace_id": trace_id,
                        "name": eval_name,
                        "value": eval_value,
                        "data_type": "NUMERIC",
                    }
                    if eval_comment:
                        score_kwargs["comment"] = eval_comment
                    ctx.client.create_score(**score_kwargs)

                # Collect for return
                if isinstance(eval_result, dict):
                    all_scores[f"{item_key}_{eval_result.get('name', 'unknown')}"] = (
                        eval_result.get("value", 0.0)
                    )
                else:
                    all_scores[f"{item_key}_{eval_result.name}"] = eval_result.value

            # Include pipeline output for disk persistence
            all_scores[f"{item_key}_output"] = output

    print(f"Theme Generation Eval Results: {ctx.session_id}")
    return all_scores


async def _run_local_fallback(config: DatasetConfig, llm, judge_llm=None) -> dict:
    """Run evaluation without Langfuse (local development).

    Calls the same evaluators as `_run_with_langfuse` (groundedness, coverage,
    specificity, redundancy) instead of the separate `metrics.py` calculation,
    so local and Langfuse runs score generation identically. LLM-based
    evaluators run concurrently via asyncio.gather(); each already catches its
    own errors internally.

    Args:
        config: DatasetConfig
        llm: LLM instance
        judge_llm: Optional dedicated judge LLM (defaults to task llm)

    Returns:
        Dict containing evaluation scores
    """
    data_items = load_local_data(config)
    all_scores = {}

    # Use dedicated judge LLM if provided, otherwise fall back to task LLM
    eval_llm = judge_llm or llm

    # Create evaluator functions
    groundedness_evaluator = create_groundedness_evaluator(eval_llm)
    coverage_evaluator = create_coverage_evaluator(eval_llm)
    specificity_evaluator = create_title_specificity_evaluator(eval_llm)
    redundancy_evaluator = create_redundancy_evaluator()

    for item in data_items:
        question_part = item.get("metadata", {}).get("question_part", "unknown")
        responses_df = pd.DataFrame(item["input"]["responses"])
        question = item["input"]["question"]
        expected_output = item["expected_output"]

        themes_df, _ = await theme_generation(
            responses_df=responses_df,
            llm=llm,
            question=question,
        )
        condensed_df, _ = await theme_condensation(
            themes_df,
            llm=llm,
            question=question,
        )
        refined_df, _ = await theme_refinement(
            condensed_df,
            llm=llm,
            question=question,
        )

        output = _build_output(refined_df)

        llm_results = await asyncio.gather(
            groundedness_evaluator(output=output, expected_output=expected_output),
            coverage_evaluator(output=output, expected_output=expected_output),
            specificity_evaluator(output=output, expected_output=expected_output),
        )
        redundancy_result = redundancy_evaluator(
            output=output, expected_output=expected_output
        )
        eval_results = [*llm_results, redundancy_result]

        for eval_result in eval_results:
            if isinstance(eval_result, dict):
                name = eval_result.get("name", "unknown")
                value = eval_result.get("value", 0.0)
            else:
                name = eval_result.name
                value = eval_result.value
            all_scores[f"{question_part}_{name}"] = value
            print(f"  {question_part}/{name}: {value}")

        # Include pipeline output for disk persistence, matching _run_with_langfuse
        all_scores[f"{question_part}_output"] = output

    print("Theme Generation Eval Results (local)")
    return all_scores


if __name__ == "__main__":
    import nest_asyncio

    nest_asyncio.apply()

    parser = argparse.ArgumentParser(description="Run theme generation evaluation")
    parser.add_argument(
        "--dataset",
        default="gambling_XS",
        help="Dataset identifier (e.g., gambling_XS)",
    )
    args = parser.parse_args()

    asyncio.run(evaluate_generation(dataset=args.dataset))
