import json
from unittest.mock import AsyncMock

import pytest
import run_eval


def test_cli_runs_selected_component_and_prints_results(monkeypatch, capsys):
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.75})
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)

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


def test_cli_rejects_unknown_component():
    with pytest.raises(SystemExit):
        run_eval.main(["--component", "unknown"])
