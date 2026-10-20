"""Task and evaluator configuration for end-to-end theme finding."""

from typing import Any

import pandas as pd
from adapters.evaluators.coverage_evaluator import CoverageEvaluator
from adapters.evaluators.groundedness_evaluator import GroundednessEvaluator
from adapters.evaluators.redundancy_evaluator import RedundancyEvaluator
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from eval_types import ComponentConfig

from themefinder import theme_condensation, theme_generation, theme_refinement


def _build_output(refined_df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Normalise generated themes into the shape consumed by the evaluators."""
    themes = []
    for record in refined_df.to_dict(orient="records"):
        if "topic" in record and ":" in record["topic"]:
            label, description = record["topic"].split(":", 1)
            record["topic_label"] = label.strip()
            record["topic_description"] = description.strip()
        themes.append(record)
    return {"themes": themes}


async def run_find_themes_task(inputs: dict, llm: Any) -> dict:
    """Run generation, condensation and refinement from responses to final themes."""
    responses_df = pd.DataFrame(inputs["responses"])
    question = inputs["question"]

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
    return _build_output(refined_df)


def build_find_themes_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh end-to-end theme-finding configuration for one evaluation run."""
    return ComponentConfig(
        component="find_themes",
        task=run_find_themes_task,
        evaluators=[
            GroundednessEvaluator(judge_llm),
            CoverageEvaluator(judge_llm),
            TitleSpecificityEvaluator(judge_llm),
            RedundancyEvaluator(),
        ],
    )
