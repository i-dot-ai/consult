"""End-to-end coverage for environment-driven evaluation orchestration."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import config as backend_config
import pytest
from adapters.artefact_stores import LocalJSONArtefactStore
from adapters.runners import PydanticEvalsRunner
from component_runner import run_component
from datasets import DatasetConfig
from eval_types import Case, ComponentConfig, Score
from fakes import FakeArtefactStore, FakeDatasetPort, FakeEvaluatorPort
from settings import get_settings
from utils import langfuse as langfuse_utils


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


@pytest.mark.parametrize(
    ("dataset_source", "artefact_store"),
    [
        ("langfuse", "local"),
        ("local", "langfuse"),
        ("langfuse", "langfuse"),
    ],
)
async def test_environment_configuration_runs_langfuse_backend_combinations(
    monkeypatch,
    dataset_source,
    artefact_store,
):
    monkeypatch.setenv("THEMEFINDER_EVAL_ENGINE", "pydantic_evals")
    monkeypatch.setenv("THEMEFINDER_EVAL_DATASET_SOURCE", dataset_source)
    monkeypatch.setenv("THEMEFINDER_EVAL_ARTEFACT_STORE", artefact_store)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "secret")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "public")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://langfuse.example.invalid")

    context = SimpleNamespace(is_enabled=True, client=object())
    context_factory = Mock(return_value=context)

    dataset = FakeDatasetPort(
        [
            Case(
                id="question_part_1",
                inputs={"question": "What changed?"},
                expected_output=None,
                metadata={"question_part": "question_part_1"},
            )
        ]
    )
    artefacts = FakeArtefactStore()
    dataset_factory = Mock(return_value=dataset)
    artefact_factory = Mock(return_value=artefacts)

    monkeypatch.setattr(langfuse_utils, "get_langfuse_context", context_factory)
    monkeypatch.setitem(
        backend_config.DATASET_FACTORIES, dataset_source, dataset_factory
    )
    monkeypatch.setitem(
        backend_config.ARTEFACT_FACTORIES, artefact_store, artefact_factory
    )
    monkeypatch.setitem(
        backend_config.RUNNER_FACTORIES,
        "pydantic_evals",
        lambda: PydanticEvalsRunner(progress=False),
    )

    async def task(inputs, llm):
        return {"themes": {"Summary": inputs["question"]}}

    dataset_config = DatasetConfig(dataset="gambling_XS", component="generation")
    backends = backend_config.resolve_backends(
        dataset_config,
        settings=get_settings(),
    )
    results = await run_component(
        ComponentConfig(
            component="generation",
            task=task,
            evaluators=[FakeEvaluatorPort([Score("quality", 1.0)])],
        ),
        dataset_config,
        backends,
        llm=object(),
    )

    context_factory.assert_called_once()
    dataset_factory.assert_called_once()
    artefact_factory.assert_called_once()
    if dataset_source == "langfuse":
        assert dataset_factory.call_args.args[0] is context
    if artefact_store == "langfuse":
        artefact_factory.assert_called_once_with(context, True)
    assert artefacts.finished_with is not None
    assert artefacts.recorded == artefacts.finished_with[0].outcomes
    assert results == {
        "question_part_1_output": {
            "themes": {"Summary": "What changed?"},
        },
        "question_part_1_quality": 1.0,
    }
