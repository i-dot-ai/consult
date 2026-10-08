import json

import pytest
from ci import check_metrics
from components import COMPONENT_NAMES


def payload(scores, *, error=None, comment=""):
    return {
        "component": "x",
        "dataset": "d",
        "results": {},
        "errors": {},
        "outcomes": [
            {
                "case": {"id": f"c{i}"},
                "output": None,
                "error": error,
                "scores": [
                    {"name": n, "value": v, "comment": comment} for n, v in s.items()
                ],
            }
            for i, s in enumerate(scores)
        ],
    }


BASELINE = {"metrics": {"f1": {"baseline": 0.8, "tolerance": 0.1}}}


def verdict(p, baseline=BASELINE):
    return check_metrics.check_component("mapping", p, baseline)


def test_within_tolerance_passes():
    v = verdict(payload([{"f1": 0.75}, {"f1": 0.77}]))
    assert not v.invalid and not v.regressions
    assert v.rows[0].status == "ok"


def test_mean_across_cases_is_used():
    v = verdict(payload([{"f1": 0.9}, {"f1": 0.5}]))  # mean 0.7 == baseline - tol
    assert not v.regressions


def test_drop_beyond_tolerance_regresses():
    v = verdict(payload([{"f1": 0.6}]))
    assert v.regressions and v.rows[0].status == "REGRESSED"


def test_improvement_is_flagged_not_failed():
    v = verdict(payload([{"f1": 0.99}]))
    assert not v.regressions and v.rows[0].status == "IMPROVED"


LOWER = {
    "metrics": {
        "redundancy": {"baseline": 0.1, "tolerance": 0.05, "direction": "lower"}
    }
}


def test_lower_is_better_metric_regresses_when_it_rises():
    v = verdict(payload([{"redundancy": 0.3}]), LOWER)
    assert v.regressions and v.rows[0].status == "REGRESSED"


def test_lower_is_better_metric_ignores_drops_and_flags_big_ones():
    assert not verdict(payload([{"redundancy": 0.0}]), LOWER).regressions
    v = verdict(
        payload([{"redundancy": 0.0}]),
        {
            "metrics": {
                "redundancy": {"baseline": 0.5, "tolerance": 0.05, "direction": "lower"}
            }
        },
    )
    assert not v.regressions and v.rows[0].status == "IMPROVED"


def test_missing_metric_regresses():
    v = verdict(payload([{"other": 1.0}]))
    assert v.rows[0].status == "MISSING" and v.regressions


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_scores_are_invalid(bad):
    assert verdict(payload([{"f1": bad}])).invalid


def test_case_error_is_invalid():
    assert verdict(payload([{"f1": 0.8}], error="boom")).invalid


def test_zeroed_judge_score_is_invalid_not_a_low_score():
    v = verdict(payload([{"f1": 0.0}], comment="Error: judge timed out"))
    assert v.invalid


def test_no_cases_is_invalid():
    assert verdict(payload([])).invalid


def test_fallback_shaped_results_are_invalid():
    assert verdict({"component": "x", "dataset": "d", "results": {}}).invalid


def test_missing_files_are_invalid():
    assert verdict(None).invalid
    assert verdict(payload([{"f1": 0.8}]), baseline=None).invalid


def write_all(tmp_path, f1):
    results, baselines = tmp_path / "runs", tmp_path / "baselines"
    baselines.mkdir(parents=True)
    for c in COMPONENT_NAMES:
        (results / c / "d").mkdir(parents=True)
        (results / c / "d" / "results.json").write_text(
            json.dumps(payload([{"f1": f1}])), encoding="utf-8"
        )
        (baselines / f"{c}_d.json").write_text(json.dumps(BASELINE), encoding="utf-8")
    return results, baselines


def args(results, baselines, *extra):
    return [
        "--dataset",
        "d",
        "--results-dir",
        str(results),
        "--baselines-dir",
        str(baselines),
        *extra,
    ]


def test_main_exit_codes_and_summary_file(tmp_path, capsys):
    results, baselines = write_all(tmp_path, 0.8)
    summary = tmp_path / "summary.md"
    assert (
        check_metrics.main(args(results, baselines, "--summary-file", str(summary)))
        == 0
    )
    assert "| mapping | f1 |" in summary.read_text(encoding="utf-8")

    results, baselines = write_all(tmp_path / "bad", 0.1)
    assert check_metrics.main(args(results, baselines)) == 1

    (results / COMPONENT_NAMES[0] / "d" / "results.json").unlink()
    assert check_metrics.main(args(results, baselines)) == 2


def test_every_component_is_checked(tmp_path):
    results, baselines = write_all(tmp_path, 0.8)
    code, summary = check_metrics.run(results, baselines, "d")
    assert code == 0
    assert all(f"| {c} |" in summary for c in COMPONENT_NAMES)
