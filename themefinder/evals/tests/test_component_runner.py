"""Unit tests for the component orchestration pipeline."""

import pytest
from adapters.runners import InlineSequentialRunner, PydanticEvalsRunner
from component_runner import run_component
from config import EvalBackends
from datasets import DatasetConfig
from eval_types import Case, CaseOutcome, ComponentConfig, RunReport, Score
from fakes import FakeArtefactStore, FakeDatasetPort, FakeEvaluatorPort, FakeRunnerPort


async def _task(inputs: dict, llm) -> dict:
    return {"echo": inputs, "llm": llm}


def _component_config(component: str = "generation") -> ComponentConfig:
    return ComponentConfig(component=component, task=_task, evaluators=[])


def _case(case_id: str = "case-1") -> Case:
    return Case(
        id=case_id,
        inputs={"id": case_id},
        expected_output=None,
        metadata={"question_part": case_id},
    )


def _outcome(case: Case) -> CaseOutcome:
    return CaseOutcome(
        case=case,
        output={"echo": case.id},
        scores=[Score("quality", 1.0, "good")],
    )


async def test_runs_full_component_pipeline_and_returns_store_result():
    events: list[str] = []
    cases = [_case("question_part_1"), _case("question_part_2")]
    report = RunReport(
        outcomes=[_outcome(case) for case in cases],
        engine_report=object(),
    )
    expected_result = {"quality": 1.0}
    dataset = FakeDatasetPort(cases, events=events)
    runner = FakeRunnerPort(report, events=events)
    artefacts = FakeArtefactStore(events=events, result=expected_result)
    backends = EvalBackends(
        dataset=dataset,
        runner=runner,
        artefacts=artefacts,
    )
    component_config = _component_config()
    dataset_config = DatasetConfig(dataset="demo", component="generation")
    llm = object()

    result = await run_component(
        component_config,
        dataset_config,
        backends,
        llm=llm,
    )

    assert result is expected_result
    assert dataset.loaded_configs == [dataset_config]
    assert runner.calls == [(component_config, cases, llm)]
    assert artefacts.started_with == ("generation", "demo")
    assert artefacts.recorded == report.outcomes
    assert artefacts.finished_with == (report, report.engine_report)
    assert events == [
        "load_cases",
        "run",
        "start_run",
        "record_case:question_part_1",
        "record_case:question_part_2",
        "finish_run",
    ]


async def test_rejects_mismatched_component_before_loading_cases():
    dataset = FakeDatasetPort([])
    backends = EvalBackends(
        dataset=dataset,
        runner=FakeRunnerPort(RunReport(outcomes=[])),
        artefacts=FakeArtefactStore(),
    )

    with pytest.raises(ValueError, match="does not match"):
        await run_component(
            _component_config("generation"),
            DatasetConfig(dataset="demo", component="mapping"),
            backends,
            llm=object(),
        )

    assert dataset.loaded_configs == []


async def test_empty_report_is_still_finalised():
    report = RunReport(outcomes=[])
    artefacts = FakeArtefactStore(result={})
    backends = EvalBackends(
        dataset=FakeDatasetPort([]),
        runner=FakeRunnerPort(report),
        artefacts=artefacts,
    )

    result = await run_component(
        _component_config(),
        DatasetConfig(dataset="demo", component="generation"),
        backends,
        llm=object(),
    )

    assert result == {}
    assert artefacts.recorded == []
    assert artefacts.finished_with == (report, None)


async def test_dataset_failure_propagates_without_starting_artefacts():
    artefacts = FakeArtefactStore()
    backends = EvalBackends(
        dataset=FakeDatasetPort([], error=RuntimeError("dataset failed")),
        runner=FakeRunnerPort(RunReport(outcomes=[])),
        artefacts=artefacts,
    )

    with pytest.raises(RuntimeError, match="dataset failed"):
        await run_component(
            _component_config(),
            DatasetConfig(dataset="demo", component="generation"),
            backends,
            llm=object(),
        )

    assert artefacts.started_with is None


async def test_runner_failure_propagates_without_starting_artefacts():
    artefacts = FakeArtefactStore()
    backends = EvalBackends(
        dataset=FakeDatasetPort([_case()]),
        runner=FakeRunnerPort(
            RunReport(outcomes=[]), error=RuntimeError("runner failed")
        ),
        artefacts=artefacts,
    )

    with pytest.raises(RuntimeError, match="runner failed"):
        await run_component(
            _component_config(),
            DatasetConfig(dataset="demo", component="generation"),
            backends,
            llm=object(),
        )

    assert artefacts.started_with is None


async def test_recording_failure_propagates_without_finishing_run():
    case = _case()
    report = RunReport(outcomes=[_outcome(case)])
    artefacts = FakeArtefactStore(record_error=RuntimeError("record failed"))
    backends = EvalBackends(
        dataset=FakeDatasetPort([case]),
        runner=FakeRunnerPort(report),
        artefacts=artefacts,
    )

    with pytest.raises(RuntimeError, match="record failed"):
        await run_component(
            _component_config(),
            DatasetConfig(dataset="demo", component="generation"),
            backends,
            llm=object(),
        )

    assert artefacts.started_with == ("generation", "demo")
    assert artefacts.finished_with is None


@pytest.mark.parametrize("stage", ["start_run", "finish_run"])
async def test_store_lifecycle_failure_propagates(monkeypatch, stage):
    case = _case()
    report = RunReport(outcomes=[_outcome(case)])
    artefacts = FakeArtefactStore()
    backends = EvalBackends(
        dataset=FakeDatasetPort([case]),
        runner=FakeRunnerPort(report),
        artefacts=artefacts,
    )

    def fail(*args, **kwargs):
        raise RuntimeError(f"{stage} failed")

    monkeypatch.setattr(artefacts, stage, fail)

    with pytest.raises(RuntimeError, match=f"{stage} failed"):
        await run_component(
            _component_config(),
            DatasetConfig(dataset="demo", component="generation"),
            backends,
            llm=object(),
        )

    if stage == "start_run":
        assert artefacts.started_with is None
        assert artefacts.recorded == []
        assert artefacts.finished_with is None
    else:
        assert artefacts.started_with == ("generation", "demo")
        assert artefacts.recorded == report.outcomes
        assert artefacts.finished_with is None


async def test_real_runners_preserve_outcomes_scores_failures_and_filter():
    async def task(inputs, llm):
        if inputs["id"] == "bad":
            raise RuntimeError("task failed")
        return {"echo": inputs["id"]}

    scores = [Score("quality", 1.0, "deterministic")]
    component_config = ComponentConfig(
        component="generation",
        task=task,
        evaluators=[FakeEvaluatorPort(scores)],
        case_filter=lambda case: case.id != "excluded",
    )
    dataset = FakeDatasetPort(
        [
            _case("good"),
            _case("bad"),
            _case("excluded"),
        ]
    )
    reports = []
    results = []

    for runner in (InlineSequentialRunner(), PydanticEvalsRunner(progress=False)):
        artefacts = FakeArtefactStore()
        results.append(
            await run_component(
                component_config,
                DatasetConfig(dataset="demo", component="generation"),
                EvalBackends(
                    dataset=dataset,
                    runner=runner,
                    artefacts=artefacts,
                ),
                llm=object(),
            )
        )
        assert artefacts.finished_with is not None
        report, engine_report = artefacts.finished_with
        assert engine_report is report.engine_report
        assert artefacts.recorded == report.outcomes
        reports.append(report)

    assert reports[0].engine_report is None
    assert reports[1].engine_report is not None
    assert reports[0].outcomes == reports[1].outcomes
    assert (
        results[0]
        == results[1]
        == {
            "good_output": {"echo": "good"},
            "good_quality": 1.0,
            "bad_output": None,
        }
    )

    outcomes = reports[0].outcomes
    assert [outcome.case.id for outcome in outcomes] == ["good", "bad"]

    good, bad = outcomes
    assert good.output == {"echo": "good"}
    assert good.scores == scores
    assert good.error is None
    assert bad.output is None
    assert bad.scores == []
    assert bad.error is not None
    assert "task failed" in bad.error
