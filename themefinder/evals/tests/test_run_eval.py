import json
from unittest.mock import AsyncMock

import pytest
import run_eval


def test_cli_runs_selected_component_prints_and_persists_results(
    monkeypatch, capsys, tmp_path
):
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.75})
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)

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
    )
    assert json.loads(capsys.readouterr().out) == {"question_part_1_f1_score": 0.75}
    assert json.loads(
        (tmp_path / "mapping" / "demo" / "results.json").read_text(encoding="utf-8")
    ) == {"question_part_1_f1_score": 0.75}


def test_cli_rejects_unknown_component():
    with pytest.raises(SystemExit):
        run_eval.main(["--component", "unknown"])
