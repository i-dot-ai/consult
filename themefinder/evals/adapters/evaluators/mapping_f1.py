"""MappingF1Evaluator — multi-label F1 for theme-to-response mapping. No LLM call."""

from typing import Any

from eval_types import Case, Score
from sklearn import metrics
from sklearn.preprocessing import MultiLabelBinarizer

from .base import EvaluatorPort


class MappingF1Evaluator(EvaluatorPort):
    metric_names = ("f1_score",)

    async def _score(self, case: Case, output: Any) -> list[Score]:
        output_labels = output.get("labels", {})
        expected_mappings = (case.expected_output or {}).get("mappings", {})

        if not expected_mappings:
            return [Score("f1_score", 0.0, "No expected mappings")]

        response_ids = list(expected_mappings.keys())
        y_true = [expected_mappings.get(rid, []) for rid in response_ids]
        y_pred = [output_labels.get(rid, []) for rid in response_ids]

        mlb = MultiLabelBinarizer()
        all_labels = set()
        for labels in y_true + y_pred:
            all_labels.update(labels)
        mlb.fit([list(all_labels)])

        y_true_bin = mlb.transform(y_true)
        y_pred_bin = mlb.transform(y_pred)
        f1 = metrics.f1_score(y_true_bin, y_pred_bin, average="samples")

        return [
            Score(
                "f1_score",
                round(f1, 3),
                f"Evaluated on {len(response_ids)} responses",
            )
        ]
