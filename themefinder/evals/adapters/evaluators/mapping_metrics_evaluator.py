"""MappingMetricsEvaluator — deterministic multi-label mapping metrics."""

from typing import Any

import pandas as pd
from eval_types import Case, Score
from metrics import calculate_mapping_metrics

from .base import EvaluatorPort


class MappingMetricsEvaluator(EvaluatorPort):
    """Preserve the mapping metrics previously produced by the local script."""

    metric_names = (
        "f1_score",
        "accuracy_score",
        "overlap_rate",
        "f1_confidence_interval_lower",
        "f1_confidence_interval_upper",
    )

    async def _score(self, case: Case, output: Any) -> list[Score]:
        output_labels = output.get("labels", {})
        expected_mappings = (case.expected_output or {}).get("mappings", {})

        if not expected_mappings:
            return [
                Score(name, 0.0, "No expected mappings") for name in self.metric_names
            ]

        # Preserve the legacy local evaluation behaviour: mapping metrics are
        # calculated only for responses returned by theme_mapping. Responses
        # in the unprocessable dataframe therefore remain excluded, as they
        # were under the previous inner join with the mapper result.
        response_ids = [
            response_id
            for response_id in expected_mappings
            if response_id in output_labels
        ]
        comparison = pd.DataFrame(
            {
                "expected": [expected_mappings.get(rid, []) for rid in response_ids],
                "predicted": [output_labels.get(rid, []) for rid in response_ids],
            }
        )
        results = calculate_mapping_metrics(comparison, "expected", "predicted")
        lower, upper = results["f1_confidence_interval"]
        comment = f"Evaluated on {len(response_ids)} responses"

        return [
            Score("f1_score", float(results["f1_score"]), comment),
            Score("accuracy_score", float(results["accuracy_score"]), comment),
            Score("overlap_rate", float(results["overlap_rate"]), comment),
            Score("f1_confidence_interval_lower", float(lower), comment),
            Score("f1_confidence_interval_upper", float(upper), comment),
        ]
