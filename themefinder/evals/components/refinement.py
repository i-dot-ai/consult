"""Task and evaluator configuration for theme refinement."""

from typing import Any

import pandas as pd
from adapters.evaluators.refinement_quality_evaluator import (
    RefinementQualityEvaluator,
)
from eval_types import ComponentConfig

from themefinder import theme_refinement


async def run_refinement_task(inputs: dict, llm: Any) -> dict:
    """Refine the input themes using the shared component output shape."""
    themes_df = pd.DataFrame(inputs["themes"])
    refined_df, _ = await theme_refinement(
        themes_df,
        llm=llm,
        question=inputs.get("question", ""),
    )
    return {"themes": refined_df.to_dict(orient="records")}


def build_refinement_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh refinement configuration for one evaluation run."""
    return ComponentConfig(
        component="refinement",
        task=run_refinement_task,
        evaluators=[RefinementQualityEvaluator(judge_llm)],
    )
