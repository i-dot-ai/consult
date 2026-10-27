"""ClarityEvaluator — per-theme binary clarity assessment."""

from typing import Any

from .llm_judge_evaluator import PerItemBinaryEvaluator
from .prompts import load_prompt_fn


class ClarityEvaluator(PerItemBinaryEvaluator):
    """Judge each refined theme independently for simple, clear wording."""

    prompt_fn = staticmethod(load_prompt_fn("clarity"))
    metric_names = ("clarity",)
    item_plural = "themes"
    decision_name = "Clarity"

    @staticmethod
    def _get_items(output: Any) -> list[dict[str, str]]:
        return output.get("themes", [])

    @staticmethod
    def _item_label(theme: dict[str, str]) -> str:
        return theme.get("topic_label", "")

    def _build_item_prompt(self, theme: dict[str, str]) -> str:
        return self.prompt_fn(
            topic_label=theme.get("topic_label", ""),
            topic_description=theme.get("topic_description", ""),
        )

    @staticmethod
    def _failure_details(failures: list[dict[str, str]]) -> str:
        return "\nFailed:\n" + "\n".join(
            f"  {failure['label']} — {failure['reasoning']}" for failure in failures
        )
