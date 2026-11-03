import json
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest

import run_eval
from comparison import QUICK_MODEL


def _write_results_payload(output_dir, component, dataset, results, outcomes=None):
    path = output_dir / component / dataset / "results.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"results": results, "outcomes": outcomes or []}),
        encoding="utf-8",
    )


def test_cli_runs_selected_component_and_prints_results(monkeypatch, capsys, tmp_path):
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.75})
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)
    _write_results_payload(
        tmp_path,
        "mapping",
        "demo",
        {"question_part_1_f1_score": 0.75},
    )

    run_eval.main(
        [
            "--component",
            "mapping",
            "--dataset",
            "demo",
            "--question",
            "2",
        ]
    )

    evaluate.assert_awaited_once_with(
        component="mapping",
        dataset="demo",
        question_num=2,
        runs=1,
    )
    assert json.loads(capsys.readouterr().out) == {"question_part_1_f1_score": 0.75}


def test_cli_exits_nonzero_for_recorded_errors(monkeypatch, capsys, tmp_path):
    results = {"question_part_1_f1_score": 0.0}

    async def evaluate(**_):
        _write_results_payload(
            tmp_path,
            "mapping",
            "demo",
            results,
            outcomes=[{"error": "task failed", "scores": []}],
        )
        return results

    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)

    with pytest.raises(SystemExit, match="1 case or evaluator errors"):
        run_eval.main(["--component", "mapping", "--dataset", "demo"])

    assert json.loads(capsys.readouterr().out) == results


def _repeated_results(*, with_detail: bool) -> dict:
    """Flat results from a repeated run, with or without the outputs and tracks."""
    case = {"f1": 0.8, "count": 1.0, "n_themes": {"mean": 2.0, "stdev": 0.0}}
    if with_detail:
        case["tracks"] = {"counts": {"stable": 2}, "themes": [], "changes": []}
    results = {
        "question_part_1_r0_f1_score": 0.75,
        "aggregate": {
            "metrics": {"f1_score": {"mean": 0.75, "stdev": None, "n": 2}},
            "output_consistency": {
                "f1": 0.8,
                "count": 1.0,
                "by_case": {"question_part_1": case},
            },
        },
    }
    if with_detail:
        results["question_part_1_r0_output"] = {"themes": []}
    return results


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ([], _repeated_results(with_detail=False)),
        (["--verbose"], _repeated_results(with_detail=True)),
    ],
    ids=["default-hides-detail", "verbose-shows-detail"],
)
def test_cli_prints_case_outputs_and_tracks_only_when_verbose(
    monkeypatch, capsys, tmp_path, flags, expected
):
    results = _repeated_results(with_detail=True)
    monkeypatch.setattr(run_eval, "evaluate_component", AsyncMock(return_value=results))
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)
    _write_results_payload(tmp_path, "mapping", "demo", results)

    run_eval.main(["--component", "mapping", "--dataset", "demo", *flags])

    assert json.loads(capsys.readouterr().out) == expected


def test_cli_rejects_unknown_component():
    with pytest.raises(SystemExit):
        run_eval.main(["--component", "unknown"])


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--component", "mapping", "generation"],
        ["--component", "mapping", "--judge-model", "gpt-4o-uk"],
        ["--component", "mapping", "--reasoning-effort", "high"],
    ],
    ids=["no-component", "two-components", "judge-model", "reasoning-effort"],
)
def test_single_run_rejects_comparison_only_shapes(monkeypatch, argv):
    evaluate = AsyncMock(return_value={})
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)

    with pytest.raises(SystemExit):
        run_eval.main(argv)

    evaluate.assert_not_awaited()


def test_model_selector_runs_a_comparison_with_the_shared_primitive(monkeypatch):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)

    run_eval.main(
        [
            "--models",
            "gpt-4o-uk",
            "gemini-flash",
            "--component",
            "mapping",
            "generation",
            "--dataset",
            "housing_S",
            "--runs",
            "2",
            "--judge-model",
            "gpt-4.1",
        ]
    )

    run_comparison.assert_awaited_once()
    args, evaluate = run_comparison.await_args.args
    assert evaluate is run_eval.evaluate_component
    assert args.models == ["gpt-4o-uk", "gemini-flash"]
    assert args.component == ["mapping", "generation"]
    assert args.dataset == "housing_S"
    assert args.runs == 2
    assert args.judge_model == "gpt-4.1"
    assert args.reasoning_effort == ["low"]


def test_comparison_takes_the_judge_from_settings_by_default(monkeypatch):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)
    monkeypatch.setattr(
        run_eval,
        "eval_settings",
        replace(run_eval.eval_settings, judge_model="judge-from-env"),
    )

    run_eval.main(["--all", "--component", "generation"])

    args, _ = run_comparison.await_args.args
    assert args.judge_model == "judge-from-env"


def test_comparison_of_judged_components_needs_a_judge(monkeypatch):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)
    monkeypatch.setattr(
        run_eval, "eval_settings", replace(run_eval.eval_settings, judge_model=None)
    )

    with pytest.raises(SystemExit):
        run_eval.main(["--all", "--component", "generation"])

    run_comparison.assert_not_awaited()


def test_mapping_only_comparison_needs_no_judge(monkeypatch):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)
    monkeypatch.setattr(
        run_eval, "eval_settings", replace(run_eval.eval_settings, judge_model=None)
    )

    run_eval.main(["--all", "--component", "mapping"])

    run_comparison.assert_awaited_once()


def test_quick_preset_is_a_comparison_of_the_smoke_model(monkeypatch):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)

    run_eval.main(["--quick", "--component", "mapping"])

    args, _ = run_comparison.await_args.args
    assert args.models == [QUICK_MODEL]
    assert args.dataset == "gambling_XS"
    assert args.runs == 1
    assert args.component == ["mapping"]


@pytest.mark.parametrize(
    "argv",
    [
        ["--models", "gpt-4o-uk", "--all"],
        ["--all", "--question", "2"],
        ["--all", "--verbose"],
    ],
    ids=["two-selectors", "question-in-comparison", "verbose-in-comparison"],
)
def test_comparison_rejects_conflicting_flags(monkeypatch, argv):
    run_comparison = AsyncMock()
    monkeypatch.setattr(run_eval.comparison, "run_comparison", run_comparison)

    with pytest.raises(SystemExit):
        run_eval.main(argv)

    run_comparison.assert_not_awaited()
