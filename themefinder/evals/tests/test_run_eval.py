import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import run_eval


def _settings_with_artefact_store(artefact_store: str | None) -> SimpleNamespace:
    return SimpleNamespace(eval=SimpleNamespace(artefact_store=artefact_store))


def test_cli_runs_selected_component_prints_and_persists_langfuse_results(
    monkeypatch, capsys, tmp_path
):
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.75})
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)
    monkeypatch.setattr(
        run_eval,
        "get_settings",
        lambda: _settings_with_artefact_store("langfuse"),
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
    )
    assert json.loads(capsys.readouterr().out) == {"question_part_1_f1_score": 0.75}
    assert json.loads(
        (tmp_path / "mapping" / "demo" / "results.json").read_text(encoding="utf-8")
    ) == {"question_part_1_f1_score": 0.75}


@pytest.mark.parametrize("artefact_store", [None, "local"])
def test_cli_does_not_overwrite_local_artefact_store_result(
    monkeypatch, capsys, tmp_path, artefact_store
):
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.75})
    output_path = tmp_path / "mapping" / "demo" / "results.json"
    local_payload = {
        "component": "mapping",
        "dataset": "demo",
        "outcomes": [{"case": {"id": "case-1"}}],
        "results": {"question_part_1_f1_score": 0.75},
    }
    output_path.parent.mkdir(parents=True)
    output_path.write_text(json.dumps(local_payload), encoding="utf-8")
    monkeypatch.setattr(run_eval, "evaluate_component", evaluate)
    monkeypatch.setattr(run_eval, "LOCAL_EVAL_RUNS_DIR", tmp_path)
    monkeypatch.setattr(
        run_eval,
        "get_settings",
        lambda: _settings_with_artefact_store(artefact_store),
    )

    run_eval.main(["--component", "mapping", "--dataset", "demo"])

    assert json.loads(capsys.readouterr().out) == {"question_part_1_f1_score": 0.75}
    assert json.loads(output_path.read_text(encoding="utf-8")) == local_payload


def test_cli_rejects_unknown_component():
    with pytest.raises(SystemExit):
        run_eval.main(["--component", "unknown"])
