"""Tests that benchmark visualisation reads locally persisted gateway metrics."""

import pandas as pd
import pytest
from visualise_benchmark import (
    BenchmarkData,
    _html_cost_latency_processing_charts,
    aggregate_by_model,
    calculate_composite_scores,
    detect_eval_metrics,
    load_local_results,
)


def test_aggregates_and_displays_cost_gateway_latency_and_processing_time_separately():
    data = BenchmarkData(
        benchmark_id="demo",
        results_df=pd.DataFrame(
            [
                {
                    "model_tag": "model-a",
                    "eval": "generation",
                    "cost_usd": 0.01,
                    "latency_seconds": 2.0,
                    "processing_time_seconds": 3.0,
                },
                {
                    "model_tag": "model-a",
                    "eval": "mapping",
                    "cost_usd": 0.02,
                    "latency_seconds": 4.0,
                    "processing_time_seconds": 6.0,
                },
            ]
        ),
    )

    aggregated = aggregate_by_model(data)

    assert data.total_cost == pytest.approx(0.03)
    assert data.avg_latency == 3.0
    assert data.avg_processing_time == 4.5
    assert aggregated.iloc[0]["cost_usd"] == pytest.approx(0.03)
    assert aggregated.iloc[0]["latency_seconds"] == 3.0
    assert aggregated.iloc[0]["processing_time_seconds"] == 4.5

    html = _html_cost_latency_processing_charts(
        ["model-a"], [0.03], [3.0], [4.5], ["generation"], [0.01]
    )
    assert "Cost, Summed Gateway Latency & Processing Time" in html
    assert "USD" in html
    assert "Summed Gateway Latency by Model" in html
    assert "Processing Time by Model" in html


def test_uses_legacy_duration_as_processing_time_when_loading_results(
    tmp_path, monkeypatch
):
    results_dir = tmp_path / "legacy"
    results_dir.mkdir()
    pd.DataFrame([{"duration_seconds": 4.5}]).to_csv(
        results_dir / "raw_results.csv", index=False
    )
    monkeypatch.setattr("visualise_benchmark.BENCHMARK_RESULTS_DIR", tmp_path)

    results = load_local_results("legacy")

    assert results.loc[0, "processing_time_seconds"] == 4.5


def test_charts_render_missing_model_metrics_as_null():
    html = _html_cost_latency_processing_charts(
        ["model-a", "model-b"],
        [0.01, float("nan")],
        [2.0, float("nan")],
        [3.0, float("nan")],
        ["mapping"],
        [0.01],
    )

    assert "null" in html
    assert "$nan" not in html


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
