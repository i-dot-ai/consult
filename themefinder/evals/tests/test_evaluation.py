from dataclasses import replace
from unittest.mock import AsyncMock, Mock

import pytest
from components import COMPONENT_NAMES
from conftest import UNCONFIGURED_LANGFUSE
from config import EvalBackends
from datasets import DatasetConfig
from eval_types import ComponentConfig
from run_eval import evaluate_component
from settings import EvalRunSettings, EvalSettings, GatewaySettings


async def _task(inputs, llm):
    return {"inputs": inputs, "llm": llm}


def _settings() -> EvalSettings:
    return EvalSettings(
        auto_eval_model="test-model",
        environment="test",
        git_sha="abcdef0",
        gateway=GatewaySettings(url="https://gateway.invalid", api_key="key"),
        langfuse=UNCONFIGURED_LANGFUSE,
        eval=EvalRunSettings(
            engine="pydantic_evals",
            dataset_source="local",
            artefact_store="local",
        ),
        log_level="INFO",
        judge_model="judge-model",
    )


@pytest.mark.parametrize("component", COMPONENT_NAMES)
async def test_builds_component_resolves_backends_and_runs(monkeypatch, component):
    import run_eval

    task_llm = object()
    judge_llm = object()
    context = object()
    settings = _settings()
    component_config = ComponentConfig(component, _task, [])
    backends = Mock(spec=EvalBackends)
    backends.tracer = Mock()
    result = {"question_part_1_quality": 1.0}
    build = Mock(return_value=component_config)
    resolve = Mock(return_value=backends)
    run = AsyncMock(return_value=result)
    monkeypatch.setattr(run_eval, "build_component_config", build)
    monkeypatch.setattr(run_eval, "resolve_backends", resolve)
    monkeypatch.setattr(run_eval, "run_component", run)

    actual = await evaluate_component(
        component,
        "demo",
        llm=task_llm,
        judge_llm=judge_llm,
        context=context,
        settings=settings,
    )

    dataset_config = DatasetConfig(dataset="demo", component=component)
    build.assert_called_once_with(component, judge_llm=judge_llm, question_num=None)
    resolve.assert_called_once_with(
        dataset_config, settings=settings, context=context, repeat=1
    )
    run.assert_awaited_once_with(
        component_config, dataset_config, backends, llm=task_llm
    )
    assert [call.args for call in backends.tracer.observe.call_args_list] == [
        (task_llm,),
        (judge_llm,),
    ]
    assert actual is result


async def test_mapping_runs_without_a_judge(monkeypatch):
    import run_eval

    task_llm = object()
    component_config = ComponentConfig("mapping", _task, [])
    monkeypatch.setattr(
        run_eval,
        "build_component_config",
        build := Mock(return_value=component_config),
    )
    monkeypatch.setattr(run_eval, "resolve_backends", Mock(return_value=Mock()))
    monkeypatch.setattr(run_eval, "run_component", AsyncMock(return_value={}))

    settings = replace(_settings(), judge_model=None)
    await evaluate_component("mapping", llm=task_llm, settings=settings)

    build.assert_called_once_with("mapping", judge_llm=None, question_num=None)


async def test_judged_component_requires_a_judge_model(monkeypatch):
    """The task model must never stand in as the judge."""
    import run_eval

    create_llm = Mock()
    monkeypatch.setattr(run_eval, "_create_llm", create_llm)

    with pytest.raises(ValueError, match="AUTO_EVAL_JUDGE_MODEL"):
        await evaluate_component(
            "generation", llm=object(), settings=replace(_settings(), judge_model=None)
        )

    create_llm.assert_not_called()


async def test_uses_patched_eval_settings_by_default(monkeypatch):
    import run_eval

    settings = _settings()
    task_llm = object()
    resolve = Mock(return_value=Mock())
    monkeypatch.setattr(run_eval, "eval_settings", settings)
    monkeypatch.setattr(
        run_eval,
        "build_component_config",
        Mock(return_value=ComponentConfig("generation", _task, [])),
    )
    monkeypatch.setattr(run_eval, "resolve_backends", resolve)
    monkeypatch.setattr(run_eval, "run_component", AsyncMock(return_value={}))

    await evaluate_component("generation", llm=task_llm)

    assert resolve.call_args.kwargs["settings"] is settings


async def test_warns_when_mapping_is_given_a_judge_llm(monkeypatch):
    import run_eval

    task_llm = object()
    judge_llm = object()
    warning = Mock()
    monkeypatch.setattr(run_eval.logger, "warning", warning)
    monkeypatch.setattr(
        run_eval,
        "build_component_config",
        Mock(return_value=ComponentConfig("mapping", _task, [])),
    )
    monkeypatch.setattr(run_eval, "resolve_backends", Mock(return_value=Mock()))
    monkeypatch.setattr(run_eval, "run_component", AsyncMock(return_value={}))

    await evaluate_component(
        "mapping",
        llm=task_llm,
        judge_llm=judge_llm,
        settings=_settings(),
    )

    warning.assert_called_once_with(
        "judge_llm is ignored for mapping because it has no judge evaluator"
    )


async def test_creates_task_and_judge_llms_from_same_settings_snapshot(monkeypatch):
    import run_eval

    settings = _settings()
    llms = {"test-model": object(), "judge-model": object()}
    component_config = ComponentConfig("generation", _task, [])
    create_llm = Mock(side_effect=lambda _settings, model: llms[model])
    build = Mock(return_value=component_config)
    resolve = Mock(return_value=Mock())
    run = AsyncMock(return_value={})
    monkeypatch.setattr(run_eval, "_create_llm", create_llm)
    monkeypatch.setattr(run_eval, "build_component_config", build)
    monkeypatch.setattr(run_eval, "resolve_backends", resolve)
    monkeypatch.setattr(run_eval, "run_component", run)

    await evaluate_component("generation", settings=settings)

    assert [c.args for c in create_llm.call_args_list] == [
        (settings, "judge-model"),
        (settings, "test-model"),
    ]
    build.assert_called_once_with(
        "generation", judge_llm=llms["judge-model"], question_num=None
    )
    assert resolve.call_args.kwargs["settings"] is settings
    assert run.await_args.kwargs["llm"] is llms["test-model"]


async def test_rejects_unknown_component_before_creating_llm(monkeypatch):
    import run_eval

    create_llm = Mock()
    monkeypatch.setattr(run_eval, "_create_llm", create_llm)

    with pytest.raises(ValueError, match="Unknown component"):
        await evaluate_component("unknown", settings=_settings())

    create_llm.assert_not_called()
