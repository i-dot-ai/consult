import json

import pytest
from ci import build_baselines, check_metrics
from components import COMPONENT_NAMES


def write_run(root, f1, *, error=None, metric="f1"):
    for component in COMPONENT_NAMES:
        path = root / component / "d" / "results.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "outcomes": [
                        {
                            "error": error,
                            "scores": [{"name": metric, "value": f1, "comment": ""}],
                        }
                    ],
                    "errors": {},
                }
            ),
            encoding="utf-8",
        )


def test_baseline_is_mean_and_tolerance_scales_with_spread(tmp_path):
    runs = [tmp_path / f"run{i}" for i in range(3)]
    for run, f1 in zip(runs, (0.5, 0.7, 0.9)):
        write_run(run, f1)

    metrics = build_baselines.build_baseline("mapping", runs, "d", 1.0, 0.05, 0.5)

    assert metrics == {"f1": {"baseline": 0.7, "tolerance": 0.2}}


def test_tolerance_floor_depends_on_metric_scale(tmp_path):
    runs = [tmp_path / "a", tmp_path / "b"]
    for run in runs:
        write_run(run, 0.8)
    judge_runs = [tmp_path / "c", tmp_path / "d"]
    for run in judge_runs:
        write_run(run, 5.0)

    unit = build_baselines.build_baseline("mapping", runs, "d", 3.0, 0.05, 0.5)
    judge = build_baselines.build_baseline("mapping", judge_runs, "d", 3.0, 0.05, 0.5)

    assert unit["f1"]["tolerance"] == 0.05
    assert judge["f1"]["tolerance"] == 0.5


def test_lower_is_better_metrics_record_their_direction(tmp_path):
    runs = [tmp_path / "a", tmp_path / "b"]
    for run in runs:
        write_run(run, 0.0, metric="redundancy")

    metrics = build_baselines.build_baseline("mapping", runs, "d", 3.0, 0.05, 0.5)

    assert metrics["redundancy"]["direction"] == "lower"


def test_runs_with_errors_are_rejected(tmp_path):
    runs = [tmp_path / "a", tmp_path / "b"]
    write_run(runs[0], 0.8)
    write_run(runs[1], 0.8, error="boom")

    with pytest.raises(ValueError, match="errors"):
        build_baselines.build_baseline("mapping", runs, "d", 3.0, 0.05, 0.5)


def test_main_writes_files_the_gate_accepts(tmp_path):
    runs = [tmp_path / "a", tmp_path / "b", tmp_path / "c"]
    for run, f1 in zip(runs, (0.78, 0.8, 0.82)):
        write_run(run, f1)
    out = tmp_path / "baselines"

    build_baselines.main(
        ["--dataset", "d", "--runs", *map(str, runs), "--out", str(out)]
    )

    assert (
        check_metrics.main(
            [
                "--dataset",
                "d",
                "--results-dir",
                str(runs[0]),
                "--baselines-dir",
                str(out),
            ]
        )
        == 0
    )
