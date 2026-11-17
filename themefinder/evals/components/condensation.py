"""Task and evaluator configuration for theme condensation."""

from typing import Any

import pandas as pd
from themefinder import theme_condensation

from adapters.evaluators.clarity_evaluator import ClarityEvaluator
from adapters.evaluators.ground_information_evaluator import (
    GroundednessInformationRetentionEvaluator,
)
from adapters.evaluators.redundancy_evaluator import RedundancyEvaluator
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from components.theme_output import build_themes_output
from eval_types import ComponentConfig


async def run_condensation_task(inputs: dict, llm: Any) -> dict:
    """Condense the input themes using the shared component output shape."""
    themes_df = pd.DataFrame(inputs["themes"])
    condensed_df, _ = await theme_condensation(
        themes_df,
        llm=llm,
        question=inputs["question"],
    )
    return build_themes_output(condensed_df)


def build_condensation_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh condensation configuration for one evaluation run."""
    return ComponentConfig(
        component="condensation",
        task=run_condensation_task,
        evaluators=[
            GroundednessInformationRetentionEvaluator(
                judge_llm, ground_truth_attr="inputs"
            ),
            ClarityEvaluator(judge_llm),
            TitleSpecificityEvaluator(judge_llm),
            RedundancyEvaluator(),
        ],
    )
