import argparse
import logging
from unittest.mock import AsyncMock

import pytest

import comparison
from conftest import make_gateway_model, set_gateway_credentials
from eval_types import RunLabels


def _args(models=None, family=None, all_=False, **extra):
    return argparse.Namespace(models=models, family=family, all=all_, **extra)


class TestModelConfigTag:
    def test_plain_name_when_no_reasoning_effort(self):
        config = comparison.ModelConfig(name="gpt-4o-uk")
        assert config.tag == "gpt-4o-uk"

    def test_appends_reasoning_effort(self):
        config = comparison.ModelConfig(
            name="gpt-5-mini-sweden", reasoning_effort="low"
        )
        assert config.tag == "gpt-5-mini-sweden_low"


class TestModelConfigCreateLlm:
    def test_sets_temperature_when_no_reasoning_effort(self, monkeypatch):
        set_gateway_credentials(monkeypatch)
        config = comparison.ModelConfig(name="gpt-4o-uk", temperature=0.2)
        llm = config.create_llm()
        assert llm.model == "gpt-4o-uk"
        assert llm.request_kwargs == {"temperature": 0.2}
        assert llm.langfuse_client is None

    def test_omits_temperature_when_reasoning_effort_set(self, monkeypatch):
        set_gateway_credentials(monkeypatch)
        config = comparison.ModelConfig(
            name="gpt-5-mini-sweden", reasoning_effort="low"
        )
        llm = config.create_llm()
        assert llm.model == "gpt-5-mini-sweden"
        assert llm.request_kwargs == {}


async def test_run_delegates_to_evaluate_with_labels_and_no_platform(monkeypatch):
    task_llm = object()
    model = comparison.ModelConfig(name="test-model")
    monkeypatch.setattr(model, "create_llm", lambda: task_llm)
    timings = iter([100.0, 107.5])
    monkeypatch.setattr(comparison.time, "perf_counter", lambda: next(timings))
    evaluate = AsyncMock(
        return_value={
            "question_part_1_f1_score": 0.75,
            "question_part_1_output": {"labels": {"1": ["A"]}},
            "metrics": {
                "cost_usd": 0.0123,
                "latency_seconds": 4.5,
                "processing_time_seconds": 5.25,
                "llm_call_count": 3,
                "input_tokens": 100,
                "output_tokens": 25,
                "total_tokens": 125,
            },
        }
    )
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(dataset="demo", models=[model]), evaluate
    )

    result = await runner._execute_eval(
        model,
        run_number=1,
        component="mapping",
        error_counter=comparison.ValidationErrorCounter("test-model"),
        judge_llm=None,
    )

    session_id = f"benchmark_{runner.comparison_id}_test-model_mapping_run1"
    evaluate.assert_awaited_once_with(
        component="mapping",
        dataset="demo",
        llm=task_llm,
        judge_llm=None,
        labels=RunLabels(
            name=session_id,
            tags=("model:test-model", "run:1", f"benchmark:{runner.comparison_id}"),
            metadata={
                "benchmark_id": runner.comparison_id,
                "model": "test-model",
                "model_tag": "test-model",
                "reasoning_effort": None,
                "run_number": 1,
            },
        ),
    )
    assert result.session_id == session_id
    assert result.scores["question_part_1_f1_score"] == 0.75
    assert result.outputs["question_part_1_output"] == {"labels": {"1": ["A"]}}
    assert result.cost_usd == 0.0123
    assert result.latency_seconds == 4.5
    assert result.duration_seconds == 7.5
    assert result.processing_time_seconds == 5.25
    assert result.llm_call_count == 3


async def test_judge_model_is_built_once_per_model_and_passed_to_every_run(
    monkeypatch, tmp_path
):
    set_gateway_credentials(monkeypatch)
    model = comparison.ModelConfig(name="test-model")
    monkeypatch.setattr(model, "create_llm", lambda: object())
    evaluate = AsyncMock(return_value={"question_part_1_f1_score": 0.5})
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(
            dataset="demo",
            models=[model],
            runs_per_model=2,
            components=["generation", "mapping"],
            judge_model="judge-model",
        ),
        evaluate,
        output_dir=str(tmp_path),
    )

    await runner._run_model(model)

    judges_by_component = {}
    for call in evaluate.await_args_list:
        judges_by_component.setdefault(call.kwargs["component"], []).append(
            call.kwargs["judge_llm"]
        )
    first_judge, second_judge = judges_by_component["generation"]
    assert first_judge is second_judge
    assert first_judge.model == "judge-model"
    assert first_judge.request_kwargs == {"temperature": 0}
    assert judges_by_component["mapping"] == [None, None]


class TestValidationErrorCounter:
    def test_counts_only_records_from_its_own_models_runs(self):
        # The library's batch processor logs its retries under this name.
        logger = logging.getLogger("theme_finder.tasks")
        first = comparison.ValidationErrorCounter("first-model")
        second = comparison.ValidationErrorCounter("second-model")
        logger.addHandler(first)
        logger.addHandler(second)
        try:
            token = comparison._run_context.set(("first-model", "mapping", 1))
            logger.warning("validation error: output did not match the schema")
            logger.warning("retrying the batch")
            comparison._run_context.reset(token)
            logger.warning("outside any run")
        finally:
            logger.removeHandler(first)
            logger.removeHandler(second)

        assert (first.validation_errors, first.total_warnings) == (1, 2)
        assert (second.validation_errors, second.total_warnings) == (0, 0)


async def test_run_lets_info_through_and_restores_the_root_logger(
    monkeypatch, tmp_path
):
    root_logger = logging.getLogger()
    original_level = root_logger.level
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(dataset="demo", models=[]),
        AsyncMock(),
        output_dir=str(tmp_path),
    )
    levels_during_run = []

    async def record_level():
        levels_during_run.append(root_logger.level)
        return []

    monkeypatch.setattr(runner, "_run_comparison", record_level)

    await runner.run()

    assert levels_during_run == [min(original_level, logging.INFO)]
    assert root_logger.level == original_level
    assert not any(
        getattr(handler, "baseFilename", "").endswith("benchmark.log")
        for handler in root_logger.handlers
    )


async def test_run_model_retries_transient_errors_and_gives_up_on_others(
    monkeypatch, tmp_path
):
    model = comparison.ModelConfig(name="test-model")
    monkeypatch.setattr(model, "create_llm", lambda: object())
    sleeps = []

    async def record_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(comparison.asyncio, "sleep", record_sleep)
    attempts = []

    async def evaluate(**kwargs):
        attempts.append(kwargs["component"])
        if len(attempts) == 1:
            raise RuntimeError("503 Service Unavailable")
        if kwargs["component"] == "generation":
            raise RuntimeError("the gateway rejected the request")
        return {"question_part_1_f1_score": 0.5}

    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(
            dataset="demo",
            models=[model],
            runs_per_model=1,
            components=["mapping", "generation"],
        ),
        evaluate,
        output_dir=str(tmp_path),
    )

    results = await runner._run_model(model)

    assert [result.component for result in results] == ["mapping"]
    assert attempts == ["mapping", "mapping", "generation"]
    assert sleeps == [2.0]
    assert (tmp_path / runner.comparison_id / "raw_results.csv").exists()


class _RunnerWithResults:
    """Stands in for ComparisonRunner so run_comparison's reporting can be exercised alone."""

    def __init__(self, config, evaluate, results):
        self.config = config
        self.results = results
        self.comparison_id = "20260101_000000"
        self.saved = False

    async def run(self):
        return self.results

    def print_results_table(self):
        pass

    def generate_summary_table(self):
        return comparison.pd.DataFrame()

    def save_results(self):
        self.saved = True

    def get_output_path(self):
        return comparison.Path("benchmark_results") / self.comparison_id


def _install_runner_with_results(monkeypatch, results):
    """Make run_comparison build a stand-in runner, and hand back every one it builds."""
    built = []

    def build(config, evaluate):
        runner = _RunnerWithResults(config, evaluate, results)
        built.append(runner)
        return runner

    monkeypatch.setattr(comparison, "ComparisonRunner", build)
    monkeypatch.setattr(
        comparison,
        "select_models",
        AsyncMock(return_value=[comparison.ModelConfig(name="test-model")]),
    )
    return built


def _comparison_args(**extra):
    return _args(
        models=["test-model"],
        component=None,
        dataset="demo",
        runs=1,
        judge_model=None,
        **extra,
    )


async def test_run_comparison_exits_when_no_result_was_collected(monkeypatch):
    _install_runner_with_results(monkeypatch, [])

    with pytest.raises(SystemExit) as exit_info:
        await comparison.run_comparison(_comparison_args(), AsyncMock())

    assert exit_info.value.code == 1


async def test_run_comparison_saves_and_prints_the_id_for_ci(monkeypatch, capsys):
    built = _install_runner_with_results(monkeypatch, [object()])

    await comparison.run_comparison(_comparison_args(), AsyncMock())

    assert built[0].saved
    assert "BENCHMARK_ID=20260101_000000" in capsys.readouterr().out.splitlines()


def test_summary_table_keeps_the_benchmark_csv_columns():
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(dataset="demo", models=[]), AsyncMock()
    )
    runner.results = [
        comparison.RunResult(
            model="test-model",
            model_tag="test-model",
            run_number=1,
            component="mapping",
            dataset="demo",
            session_id="session",
            scores={"f1": 0.5},
            timestamp=comparison.datetime.now(),
            duration_seconds=5.25,
            processing_time_seconds=5.25,
        )
    ]

    summary = runner.generate_summary_table()

    assert summary.loc[0, "eval"] == "mapping"
    assert summary.loc[0, "duration_seconds"] == 5.25
    assert summary.loc[0, "processing_time_seconds"] == 5.25
    assert summary.loc[0, "f1"] == 0.5


def test_saves_results_under_the_benchmark_results_layout(tmp_path):
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(
            dataset="demo",
            models=[comparison.ModelConfig(name="test-model")],
            runs_per_model=1,
            components=["mapping"],
        ),
        AsyncMock(),
        output_dir=str(tmp_path),
    )
    runner.results = [
        comparison.RunResult(
            model="test-model",
            model_tag="test-model",
            run_number=1,
            component="mapping",
            dataset="demo",
            session_id="session",
            scores={"f1": 0.5},
            outputs={"question_part_1_output": {"labels": {}}},
            timestamp=comparison.datetime.now(),
        )
    ]

    runner._save_config()
    runner._save_incremental()
    runner._save_outputs(runner.results[0])
    runner.save_results()

    output_path = tmp_path / runner.comparison_id
    assert (output_path / "raw_results.csv").exists()
    assert (output_path / "aggregated_results.csv").exists()
    assert (output_path / "outputs" / "test-model_mapping_run1.json").exists()
    config = comparison.json.loads((output_path / "config.json").read_text())
    assert config["benchmark_id"] == runner.comparison_id
    assert config["evals"] == ["mapping"]
    assert config["models"] == [{"name": "test-model", "reasoning_effort": None}]


class TestToModelConfigs:
    def test_non_reasoning_model_ignores_effort_levels(self):
        gateway_model = make_gateway_model(name="gpt-4o-uk", supports_reasoning=False)
        configs = comparison.to_model_configs(gateway_model, ["low", "medium", "high"])
        assert len(configs) == 1
        assert configs[0].name == "gpt-4o-uk"
        assert configs[0].reasoning_effort is None

    def test_reasoning_model_expands_per_effort_level(self):
        gateway_model = make_gateway_model(
            name="gpt-5-mini-sweden", supports_reasoning=True
        )
        configs = comparison.to_model_configs(gateway_model, ["low", "medium", "high"])
        assert [config.tag for config in configs] == [
            "gpt-5-mini-sweden_low",
            "gpt-5-mini-sweden_medium",
            "gpt-5-mini-sweden_high",
        ]


class TestIsComparison:
    def test_single_run_without_selectors(self):
        assert comparison.is_comparison(_args(quick=False)) is False

    def test_any_selector_or_quick(self):
        assert comparison.is_comparison(_args(models=["gpt-4o-uk"], quick=False))
        assert comparison.is_comparison(_args(family=["gpt"], quick=False))
        assert comparison.is_comparison(_args(all_=True, quick=False))
        assert comparison.is_comparison(_args(quick=True))


class TestApplyQuickPreset:
    def test_noop_when_not_quick(self):
        args = _args(all_=True, quick=False, dataset="housing_S", runs=5)
        comparison.apply_quick_preset(args)
        assert args.dataset == "housing_S"
        assert args.runs == 5
        assert args.all is True

    def test_overrides_other_selectors_when_quick(self):
        args = _args(
            models=["something"],
            family=["gpt"],
            quick=True,
            dataset="housing_S",
            runs=5,
        )
        comparison.apply_quick_preset(args)
        assert args.dataset == "gambling_XS"
        assert args.runs == 1
        assert args.models == [comparison.QUICK_MODEL]
        assert args.family is None
        assert args.all is False


class TestValidateSelectorArgs:
    def test_exactly_one_selector_is_valid(self):
        assert comparison.validate_selector_args(_args(models=["gpt-4o-uk"])) is None

    def test_no_selector_is_invalid(self):
        assert comparison.validate_selector_args(_args()) is not None

    def test_multiple_selectors_is_invalid(self):
        args = _args(models=["gpt-4o-uk"], family=["gpt"])
        assert comparison.validate_selector_args(args) is not None


MODELS = [
    make_gateway_model(name="gpt-4o-uk", family="gpt"),
    make_gateway_model(name="claude-haiku", family="claude", health="unhealthy"),
    make_gateway_model(name="gemini-flash", family="gemini"),
]


class TestSelectNamedModels:
    def test_returns_found_and_missing(self):
        selected, missing, unhealthy = comparison.select_named_models(
            MODELS, ["gpt-4o-uk", "typo-model"]
        )
        assert [model.name for model in selected] == ["gpt-4o-uk"]
        assert missing == ["typo-model"]
        assert unhealthy == []

    def test_reports_unhealthy_matches_but_still_selects_them(self):
        selected, missing, unhealthy = comparison.select_named_models(
            MODELS, ["claude-haiku"]
        )
        assert [model.name for model in selected] == ["claude-haiku"]
        assert missing == []
        assert [model.name for model in unhealthy] == ["claude-haiku"]


class TestSelectHealthyModels:
    def test_family_excludes_unhealthy(self):
        selected, excluded = comparison.select_healthy_models(MODELS, ["claude"])
        assert selected == []
        assert [model.name for model in excluded] == ["claude-haiku"]

    def test_no_family_excludes_unhealthy_and_returns_the_rest(self):
        selected, excluded = comparison.select_healthy_models(MODELS, None)
        assert {model.name for model in selected} == {"gpt-4o-uk", "gemini-flash"}
        assert [model.name for model in excluded] == ["claude-haiku"]


class TestSelectModels:
    async def test_named_selection_dedupes_and_expands_reasoning(self, monkeypatch):
        reasoning = make_gateway_model(name="gpt-5-mini", supports_reasoning=True)
        monkeypatch.setattr(
            comparison.gateway,
            "discover_chat_models",
            AsyncMock(return_value=[*MODELS, reasoning]),
        )
        args = _args(
            models=["gpt-5-mini", "gpt-5-mini", "gpt-4o-uk"],
            reasoning_effort=["low", "high"],
        )

        models = await comparison.select_models(args)

        assert [model.tag for model in models] == [
            "gpt-5-mini_low",
            "gpt-5-mini_high",
            "gpt-4o-uk",
        ]

    async def test_missing_name_exits(self, monkeypatch):
        monkeypatch.setattr(
            comparison.gateway, "discover_chat_models", AsyncMock(return_value=MODELS)
        )

        try:
            await comparison.select_models(
                _args(models=["typo-model"], reasoning_effort=["low"])
            )
        except SystemExit as exit_request:
            assert exit_request.code == 1
        else:
            raise AssertionError("expected a SystemExit")

    async def test_family_selection_drops_unhealthy(self, monkeypatch):
        monkeypatch.setattr(
            comparison.gateway, "discover_chat_models", AsyncMock(return_value=MODELS)
        )

        models = await comparison.select_models(
            _args(family=["gpt", "claude"], reasoning_effort=["low"])
        )

        assert [model.name for model in models] == ["gpt-4o-uk"]
