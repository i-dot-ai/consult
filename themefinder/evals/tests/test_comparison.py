import argparse
from unittest.mock import AsyncMock

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
        error_counter=comparison.ValidationErrorCounter(),
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


async def test_judge_model_becomes_a_separate_llm(monkeypatch):
    set_gateway_credentials(monkeypatch)
    model = comparison.ModelConfig(name="test-model")
    monkeypatch.setattr(model, "create_llm", lambda: object())
    evaluate = AsyncMock(return_value={})
    runner = comparison.ComparisonRunner(
        comparison.ComparisonConfig(
            dataset="demo", models=[model], judge_model="judge-model"
        ),
        evaluate,
    )

    await runner._execute_eval(
        model,
        run_number=1,
        component="generation",
        error_counter=comparison.ValidationErrorCounter(),
    )

    judge_llm = evaluate.await_args.kwargs["judge_llm"]
    assert judge_llm.model == "judge-model"
    assert judge_llm.request_kwargs == {"temperature": 0}


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
