"""Tests for Information Equivalence benchmark visualisation."""

import pandas as pd
from visualise_benchmark import (
    BenchmarkData,
    calculate_composite_scores,
    detect_eval_metrics,
)


def test_refinement_information_equivalence_is_detected_and_scaled_from_zero_to_one():
    results = pd.DataFrame(
        {
            "model_tag": ["test-model"],
            "eval": ["refinement"],
            "question_part_1_information_equivalence": [0.5],
            "question_part_1_response_references": [5.0],
            "question_part_1_distinctiveness": [5.0],
            "question_part_1_fluency": [5.0],
        }
    )
    refinement_metrics = detect_eval_metrics(results, "refinement")
    data = BenchmarkData(
        benchmark_id="test",
        results_df=results,
        detected_metrics={"refinement": refinement_metrics},
    )

    scores = calculate_composite_scores(data)

    assert refinement_metrics == {
        "information_equivalence": ["question_part_1_information_equivalence"],
        "response_references": ["question_part_1_response_references"],
        "distinctiveness": ["question_part_1_distinctiveness"],
        "fluency": ["question_part_1_fluency"],
    }
    assert scores.loc[0, "refinement_score"] == 0.875
