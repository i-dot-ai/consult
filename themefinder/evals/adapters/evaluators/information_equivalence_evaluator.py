"""InformationEquivalenceEvaluator — bidirectional exact-one theme matching."""

from typing import Any

from eval_types import Case, Score
from prompts.refinement import information_equivalence_match_prompt

from .llm_judge_evaluator import BinaryMatchJudgeEvaluator


class InformationEquivalenceEvaluator(BinaryMatchJudgeEvaluator):
    """Score reciprocal one-to-one correspondence between original and refined themes."""

    metric_names = ("information_equivalence",)
    prompt_fn = staticmethod(information_equivalence_match_prompt)

    @staticmethod
    def _format_theme(theme: Any) -> str:
        """Preserve a theme's label and description in the binary judge input."""
        if isinstance(theme, str):
            return theme
        if not isinstance(theme, dict):
            return str(theme)

        if theme.get("topic"):
            return str(theme["topic"])

        label = str(theme.get("topic_label", "")).strip()
        description = str(theme.get("topic_description", "")).strip()
        return f"{label}: {description}" if description else label

    def _get_lists(self, case: Case, output: Any) -> tuple[list[str], list[str]]:
        original_themes = case.inputs.get("themes", [])
        refined_themes = output.get("themes", [])
        return (
            [self._format_theme(theme) for theme in original_themes],
            [self._format_theme(theme) for theme in refined_themes],
        )

    def _build_item_prompt(self, single_item: str, item_list: list[str]) -> str:
        return self.prompt_fn(
            theme_to_match=single_item,
            candidate_themes=item_list,
        )

    async def _score(self, case: Case, output: Any) -> list[Score]:
        """Judge exact-one matching in both directions and retain reciprocal pairs."""
        original_themes, refined_themes = self._get_lists(case, output)
        refined_to_original = await self._llm_decision_loop(
            refined_themes, original_themes
        )
        original_to_refined = await self._llm_decision_loop(
            original_themes, refined_themes
        )
        return self._build_scores(
            {
                "refined_to_original": refined_to_original,
                "original_to_refined": original_to_refined,
                "refined_themes": refined_themes,
                "original_themes": original_themes,
            }
        )

    @staticmethod
    def _matching_pairs(
        decisions: list[dict[str, Any]], candidate_count: int
    ) -> list[tuple[int, int]]:
        """Return valid source/candidate index pairs from YES decisions."""
        pairs = []
        for source_index, decision in enumerate(decisions, start=1):
            if str(decision.get("decision", "")).upper() != "YES":
                continue
            try:
                candidate_index = int(decision["matched_candidate_id"])
            except (KeyError, TypeError, ValueError):
                continue
            if 1 <= candidate_index <= candidate_count:
                pairs.append((source_index, candidate_index))
        return pairs

    @staticmethod
    def _format_pairs(pairs: list[tuple[int, int]]) -> str:
        return (
            ", ".join(f"{source}→{candidate}" for source, candidate in pairs) or "none"
        )

    @staticmethod
    def _reciprocal_pairs(
        refined_to_original: list[tuple[int, int]],
        original_to_refined: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Keep only pairings confirmed by both directional judge calls."""
        reverse_pairs = {
            (refined_index, original_index)
            for original_index, refined_index in original_to_refined
        }
        return [
            (refined_index, original_index)
            for refined_index, original_index in refined_to_original
            if (refined_index, original_index) in reverse_pairs
        ]

    def _build_scores(self, decisions: Any) -> list[Score]:
        """Use mutually confirmed exact-one pairings as information equivalence."""
        refined_to_original = decisions["refined_to_original"]
        original_to_refined = decisions["original_to_refined"]
        refined_themes = decisions["refined_themes"]
        original_themes = decisions["original_themes"]
        refined_pairs = self._matching_pairs(refined_to_original, len(original_themes))
        original_pairs = self._matching_pairs(original_to_refined, len(refined_themes))
        reciprocal_pairs = self._reciprocal_pairs(refined_pairs, original_pairs)
        score = len(reciprocal_pairs) / max(len(refined_themes), len(original_themes))
        absolute_difference = abs(len(refined_themes) - len(original_themes))
        comment = (
            f"{len(reciprocal_pairs)}/{max(len(refined_themes), len(original_themes))} "
            f"reciprocal one-to-one pairs; list length difference: {absolute_difference}\n"
            f"Refined→original claimed pairs: {self._format_pairs(refined_pairs)}\n"
            f"Original→refined claimed pairs: {self._format_pairs(original_pairs)}\n"
            f"Reciprocal pairs: {self._format_pairs(reciprocal_pairs)}"
        )
        return [Score("information_equivalence", score, comment)]
