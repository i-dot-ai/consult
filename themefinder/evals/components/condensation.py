"""Task and evaluator configuration for theme condensation."""

from typing import Any

import pandas as pd
from adapters.evaluators.condensation_quality_evaluator import (
    CondensationQualityEvaluator,
)
from adapters.evaluators.redundancy_evaluator import RedundancyEvaluator
from eval_types import ComponentConfig

from themefinder import theme_condensation


async def run_condensation_task(inputs: dict, llm: Any) -> dict:
    """Condense the input themes using the established public output shape."""
    themes_df = pd.DataFrame(inputs["themes"])
    condensed_df, _ = await theme_condensation(
        themes_df,
        llm=llm,
        question=inputs["question"],
    )
    return {"condensed_themes": condensed_df.to_dict(orient="records")}


def build_condensation_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh condensation configuration for one evaluation run."""
    return ComponentConfig(
        component="condensation",
        task=run_condensation_task,
        evaluators=[
            CondensationQualityEvaluator(judge_llm),
            RedundancyEvaluator(themes_key="condensed_themes"),
        ],
    )
