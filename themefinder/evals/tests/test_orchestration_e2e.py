"""End-to-end coverage for environment-driven evaluation orchestration."""

import json

import config as backend_config
from adapters.artefact_stores import LocalJSONArtefactStore
from adapters.runners import PydanticEvalsRunner
from component_runner import run_component
from datasets import DatasetConfig
from eval_types import ComponentConfig, Score
from fakes import FakeEvaluatorPort
from settings import get_settings


async def test_environment_configuration_runs_complete_local_pipeline(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("THEMEFINDER_EVAL_ENGINE", "pydantic_evals")
    monkeypatch.setenv("THEMEFINDER_EVAL_DATASET_SOURCE", "local")
    monkeypatch.setenv("THEMEFINDER_EVAL_ARTEFACT_STORE", "local")
    monkeypatch.setitem(
        backend_config.ARTEFACT_FACTORIES,
        "local",
        lambda context, owns_context: LocalJSONArtefactStore(output_dir=tmp_path),
    )
    monkeypatch.setitem(
        backend_config.RUNNER_FACTORIES,
        "pydantic_evals",
        lambda: PydanticEvalsRunner(progress=False),
    )

    task_calls = []

    async def task(inputs, llm):
        task_calls.append((inputs, llm))
        return {"themes": {"Summary": inputs["question"]}}

    evaluator = FakeEvaluatorPort([Score("quality", 1.0, "deterministic")])
    component_config = ComponentConfig(
        component="generation",
        task=task,
        evaluators=[evaluator],
    )
    dataset_config = DatasetConfig(dataset="gambling_XS", component="generation")
    settings = get_settings()
    backends = backend_config.resolve_backends(dataset_config, settings=settings)
    llm = object()

    results = await run_component(
        component_config,
        dataset_config,
        backends,
        llm=llm,
    )

    assert settings.eval.engine == "pydantic_evals"
    assert settings.eval.dataset_source == "local"
    assert settings.eval.artefact_store == "local"
    assert len(task_calls) == 2
    assert all(call_llm is llm for _, call_llm in task_calls)
    assert len(evaluator.calls) == 2
    assert results["question_part_1_quality"] == 1.0
    assert results["question_part_2_quality"] == 1.0

    output_path = tmp_path / "generation" / "gambling_XS" / "results.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["component"] == "generation"
    assert payload["dataset"] == "gambling_XS"
    assert payload["results"] == results
    assert len(payload["outcomes"]) == 2
