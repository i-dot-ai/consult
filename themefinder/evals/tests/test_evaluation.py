from unittest.mock import AsyncMock, Mock

import pytest
from config import EvalBackends
from datasets import DatasetConfig
from eval_types import ComponentConfig
from evaluation import evaluate_component
from settings import EvalRunSettings, EvalSettings, GatewaySettings


async def _task(inputs, llm):
    return {"inputs": inputs, "llm": llm}


def _settings() -> EvalSettings:
    return EvalSettings(
        auto_eval_model="test-model",
        environment="test",
        git_sha="abcdef0",
        log_level="INFO",
        gateway=GatewaySettings(url="https://gateway.invalid", api_key="key"),
        langfuse=None,
        eval=EvalRunSettings(
            engine="pydantic_evals",
            dataset_source="local",
            artefact_store="local",
        ),
    )


async def test_builds_component_resolves_backends_and_runs(monkeypatch):
    import evaluation

    task_llm = object()
    judge_llm = object()
    context = object()
    settings = _settings()
    component_config = ComponentConfig("generation", _task, [])
    backends = Mock(spec=EvalBackends)
    result = {"question_part_1_quality": 1.0}
    build = Mock(return_value=component_config)
    resolve = Mock(return_value=backends)
    run = AsyncMock(return_value=result)
    monkeypatch.setattr(evaluation, "build_component_config", build)
    monkeypatch.setattr(evaluation, "resolve_backends", resolve)
    monkeypatch.setattr(evaluation, "run_component", run)

    actual = await evaluate_component(
        "generation",
        "demo",
        llm=task_llm,
        judge_llm=judge_llm,
        context=context,
        settings=settings,
    )

    dataset_config = DatasetConfig(dataset="demo", component="generation")
    build.assert_called_once_with("generation", judge_llm=judge_llm, question_num=None)
    resolve.assert_called_once_with(dataset_config, settings=settings, context=context)
    run.assert_awaited_once_with(
        component_config, dataset_config, backends, llm=task_llm
    )
    assert actual is result


async def test_uses_task_llm_as_judge_by_default(monkeypatch):
    import evaluation

    task_llm = object()
    component_config = ComponentConfig("mapping", _task, [])
    monkeypatch.setattr(
        evaluation,
        "build_component_config",
        build := Mock(return_value=component_config),
    )
    monkeypatch.setattr(evaluation, "resolve_backends", Mock(return_value=Mock()))
    monkeypatch.setattr(evaluation, "run_component", AsyncMock(return_value={}))

    await evaluate_component("mapping", llm=task_llm, settings=_settings())

    build.assert_called_once_with("mapping", judge_llm=task_llm, question_num=None)


async def test_creates_default_llm_from_same_settings_snapshot(monkeypatch):
    import evaluation

    settings = _settings()
    default_llm = object()
    component_config = ComponentConfig("generation", _task, [])
    create_llm = Mock(return_value=default_llm)
    build = Mock(return_value=component_config)
    resolve = Mock(return_value=Mock())
    run = AsyncMock(return_value={})
    monkeypatch.setattr(evaluation, "_create_default_llm", create_llm)
    monkeypatch.setattr(evaluation, "build_component_config", build)
    monkeypatch.setattr(evaluation, "resolve_backends", resolve)
    monkeypatch.setattr(evaluation, "run_component", run)

    await evaluate_component("generation", settings=settings)

    create_llm.assert_called_once_with(settings)
    build.assert_called_once_with(
        "generation", judge_llm=default_llm, question_num=None
    )
    assert resolve.call_args.kwargs["settings"] is settings
    assert run.await_args.kwargs["llm"] is default_llm


async def test_rejects_unknown_component_before_creating_llm(monkeypatch):
    import evaluation

    create_llm = Mock()
    monkeypatch.setattr(evaluation, "_create_default_llm", create_llm)

    with pytest.raises(ValueError, match="Unknown component"):
        await evaluate_component("unknown", settings=_settings())

    create_llm.assert_not_called()
