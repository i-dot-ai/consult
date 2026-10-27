"""TitleSpecificityEvaluator — per-title binary specificity assessment."""

from typing import Any

from .llm_judge_evaluator import PerItemBinaryEvaluator
from .prompts import load_prompt_fn


class TitleSpecificityEvaluator(PerItemBinaryEvaluator):
    """Judge each generated title independently for concrete specificity."""

    prompt_fn = staticmethod(load_prompt_fn("title_specificity"))
    metric_names = ("specificity",)
    item_plural = "titles"
    decision_name = "Specificity"

    def _get_items(self, output: Any) -> list[str]:
        return self.extract_theme_titles(output.get("themes", []))

    @staticmethod
    def _item_label(title: str) -> str:
        return title

    def _build_item_prompt(self, title: str) -> str:
        return self.prompt_fn(theme_title=title)
