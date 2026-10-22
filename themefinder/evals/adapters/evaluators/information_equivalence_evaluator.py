"""InformationEquivalenceEvaluator — bidirectional exact-one theme matching."""

from typing import Any

from eval_types import Case, Score

from .llm_judge_evaluator import BinaryMatchDecisions, BinaryMatchJudgeEvaluator


class InformationEquivalenceEvaluator(BinaryMatchJudgeEvaluator):
    """Score reciprocal one-to-one correspondence between original and refined themes."""

    metric_names = ("information_equivalence",)

    @staticmethod
    def _format_theme(theme: dict[str, str]) -> str:
        """Combine the canonical theme label and description for the judge."""
        label = theme["topic_label"].strip()
        description = theme["topic_description"].strip()
        return f"{label}: {description}" if description else label

    def _get_lists(self, case: Case, output: Any) -> tuple[list[str], list[str]]:
        original_themes = case.inputs.get("themes", [])
        refined_themes = output.get("themes", [])
        return (
            [self._format_theme(theme) for theme in original_themes],
            [self._format_theme(theme) for theme in refined_themes],
        )

    @staticmethod
    def _matching_pairs(
        decisions: list[dict[str, Any]], candidate_themes: list[str]
    ) -> list[tuple[int, int]]:
        """Return unambiguous source/candidate index pairs from PASS decisions."""
        pairs = []
        for source_index, decision in enumerate(decisions, start=1):
            if str(decision.get("decision", "")).upper() != "PASS":
                continue

            matched_items = decision.get("matched_items")
            if not isinstance(matched_items, list) or len(matched_items) != 1:
                continue

            candidate_indices = [
                index
                for index, candidate in enumerate(candidate_themes, start=1)
                if candidate == matched_items[0]
            ]
            if len(candidate_indices) == 1:
                pairs.append((source_index, candidate_indices[0]))
        return pairs

    @staticmethod
    def _format_pairs(pairs: list[tuple[int, int]]) -> str:
        return (
            ", ".join(f"{source}→{candidate}" for source, candidate in pairs) or "none"
        )

    def _build_scores(self, decisions: BinaryMatchDecisions) -> list[Score]:
        """Use mutually confirmed exact-one pairings as information equivalence."""
        original_to_refined = self._matching_pairs(
            decisions.forward, decisions.candidates
        )
        refined_to_original = self._matching_pairs(decisions.backward, decisions.items)
        reciprocal_pairs = [
            (original_index, refined_index)
            for original_index, refined_index in original_to_refined
            if (refined_index, original_index) in refined_to_original
        ]
        list_size = max(len(decisions.items), len(decisions.candidates))
        score = len(reciprocal_pairs) / list_size
        absolute_difference = abs(len(decisions.items) - len(decisions.candidates))
        comment = (
            f"{len(reciprocal_pairs)}/{list_size} reciprocal one-to-one pairs; "
            f"list length difference: {absolute_difference}\n"
            f"Original→refined claimed pairs: {self._format_pairs(original_to_refined)}\n"
            f"Refined→original claimed pairs: {self._format_pairs(refined_to_original)}\n"
            f"Reciprocal pairs: {self._format_pairs(reciprocal_pairs)}"
        )
        return [Score("information_equivalence", score, comment)]
