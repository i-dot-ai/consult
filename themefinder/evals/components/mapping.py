"""Task and evaluator configuration for response-to-theme mapping."""

from typing import Any

import pandas as pd
from adapters.evaluators.mapping_metrics_evaluator import MappingMetricsEvaluator
from eval_types import Case, ComponentConfig
from utils.logging_config import get_logger

from themefinder import theme_mapping

logger = get_logger(__name__)


async def run_mapping_task(inputs: dict, llm: Any) -> dict:
    """Assign themes to responses and return labels keyed by response id."""
    responses_df = pd.DataFrame(inputs["responses"])
    topics_df = pd.DataFrame(inputs["topics"])
    result_df, unprocessable_df = await theme_mapping(
        responses_df=responses_df[["response_id", "response"]],
        llm=llm,
        question=inputs["question"],
        refined_themes_df=topics_df[["topic_id", "topic"]],
    )

    if not unprocessable_df.empty:
        logger.warning("%s responses could not be processed", len(unprocessable_df))

    return {
        "labels": dict(
            zip(
                result_df["response_id"].astype(str),
                result_df["labels"].tolist(),
            )
        )
    }


def _matches_question(case: Case, question_num: int) -> bool:
    question_part = case.metadata.get("question_part", case.id)
    return question_part == f"question_part_{question_num}"


def build_mapping_config(*, question_num: int | None = None) -> ComponentConfig:
    """Build a fresh mapping configuration, optionally filtering one question."""
    case_filter = (
        None
        if question_num is None
        else lambda case: _matches_question(case, question_num)
    )
    return ComponentConfig(
        component="mapping",
        task=run_mapping_task,
        evaluators=[MappingMetricsEvaluator()],
        case_filter=case_filter,
    )
