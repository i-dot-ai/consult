import json
from unittest.mock import AsyncMock

import pytest

import run_eval


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
