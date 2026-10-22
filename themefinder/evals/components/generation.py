"""Task and evaluator configuration for theme generation."""

from typing import Any

import pandas as pd
from adapters.evaluators.coverage_evaluator import CoverageEvaluator
from adapters.evaluators.groundedness_evaluator import GroundednessEvaluator
from adapters.evaluators.redundancy_evaluator import RedundancyEvaluator
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from eval_types import ComponentConfig

from components._utils import build_themes_output
from themefinder import theme_generation


async def run_generation_task(inputs: dict, llm: Any) -> dict:
    """Generate candidate themes from responses."""
    responses_df = pd.DataFrame(inputs["responses"])

    themes_df, _ = await theme_generation(
        responses_df=responses_df,
        llm=llm,
        question=inputs["question"],
    )
    return build_themes_output(themes_df)


def build_generation_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh generation configuration for one evaluation run."""
    return ComponentConfig(
        component="generation",
        task=run_generation_task,
        evaluators=[
            GroundednessEvaluator(judge_llm),
            CoverageEvaluator(judge_llm),
            TitleSpecificityEvaluator(judge_llm),
            RedundancyEvaluator(),
        ],
    )
