"""GroundednessInformationRetentionEvaluator — precision, recall and F1 of generated
themes against the input or expected themes, from one pair of judge loops.

One class rather than three because F1 needs both directions and the evaluator
port gives no way to read another evaluator's scores.
"""

from eval_types import Case, Score

from .llm_judge_evaluator import BinaryMatchDecisions, BinaryMatchJudgeEvaluator


class GroundednessInformationRetentionEvaluator(BinaryMatchJudgeEvaluator):
    metric_names = ("groundedness", "information_retention", "f1_score")

    def __init__(self, *args, ground_truth_attr: str = "expected_output", **kwargs):
        super().__init__(*args, **kwargs)
        self.ground_truth_attr = ground_truth_attr

    def _get_lists(self, case: Case, output: dict) -> tuple[list[str], list[str]]:
        """Get input themes and generated themes as lists of strings for comparison."""
        case_side = getattr(case, self.ground_truth_attr) or {}
        original_themes = case_side.get("themes", [])
        output_themes = output.get("themes", [])
        return (
            [self._format_theme(theme) for theme in original_themes],
            [self._format_theme(theme) for theme in output_themes],
        )

    def _build_scores(self, decisions: BinaryMatchDecisions) -> list[Score]:
        """Score groundedness (precision), information retention (recall) and their
        harmonic mean, with the unmatched items listed in each comment."""
        precision, precision_comment = self._ratio(
            decisions.backward, "themes grounded", "Ungrounded"
        )
        recall, recall_comment = self._ratio(
            decisions.forward, "themes retained", "Lost"
        )
        both = precision + recall
        f1 = 2 * precision * recall / both if both else 0.0

        return [
            Score("groundedness", round(precision, 2), precision_comment),
            Score("information_retention", round(recall, 2), recall_comment),
            Score(
                "f1_score",
                round(f1, 2),
                f"Precision {precision:.2f}, recall {recall:.2f}",
            ),
        ]

    @staticmethod
    def _ratio(
        decisions: list[dict], noun: str, missed_label: str
    ) -> tuple[float, str]:
        """Fraction of items that passed, and a comment listing those that did not.
        No decisions scores 0.0, since there is nothing to have been matched."""

        def _passed(decision: dict) -> bool:
            return decision.get("decision") == "PASS"

        n_passed = sum(_passed(d) for d in decisions)
        ratio = n_passed / len(decisions) if decisions else 0.0

        comment = f"{n_passed}/{len(decisions)} {noun}"
        missed = [d["item"] for d in decisions if not _passed(d)]
        if missed:
            comment += f"\n{missed_label}: {', '.join(missed)}"
        return ratio, comment
