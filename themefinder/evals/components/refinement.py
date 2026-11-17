"""Task and evaluator configuration for theme refinement."""

from typing import Any

import pandas as pd
from themefinder import theme_refinement

from adapters.evaluators.clarity_evaluator import ClarityEvaluator
from adapters.evaluators.information_equivalence_evaluator import (
    InformationEquivalenceEvaluator,
)
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from components.theme_output import build_themes_output
from eval_types import ComponentConfig


async def run_refinement_task(inputs: dict, llm: Any) -> dict:
    """Refine the input themes using the shared component output shape."""
    themes_df = pd.DataFrame(inputs["themes"])
    refined_df, _ = await theme_refinement(
        themes_df,
        llm=llm,
        question=inputs.get("question", ""),
    )
    return build_themes_output(refined_df)


def build_refinement_config(judge_llm: Any) -> ComponentConfig:
    """Build a fresh refinement configuration for one evaluation run."""
    return ComponentConfig(
        component="refinement",
        task=run_refinement_task,
        evaluators=[
            ClarityEvaluator(judge_llm),
            TitleSpecificityEvaluator(judge_llm),
            InformationEquivalenceEvaluator(judge_llm),
        ],
    )
