from pathlib import Path

import pandas as pd
import pytest
from adapters.evaluators.condensation_quality_evaluator import (
    CondensationQualityEvaluator,
)
from adapters.evaluators.coverage_evaluator import CoverageEvaluator
from adapters.evaluators.groundedness_evaluator import GroundednessEvaluator
from adapters.evaluators.mapping_metrics_evaluator import MappingMetricsEvaluator
from adapters.evaluators.redundancy_evaluator import RedundancyEvaluator
from adapters.evaluators.refinement_quality_evaluator import (
    RefinementQualityEvaluator,
)
from adapters.evaluators.title_specificity_evaluator import TitleSpecificityEvaluator
from components import (
    COMPONENT_NAMES,
    build_component_config,
    condensation,
    generation,
    mapping,
    refinement,
)
from eval_types import Case


def test_workflow_component_choices_match_registry():
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / ".github" / "workflows" / "themefinder-eval.yml"
    ).read_text(encoding="utf-8")
    eval_input = workflow.split("eval_type:", maxsplit=1)[1].split(
        "default:", maxsplit=1
    )[0]
    choices = {
        line.strip().removeprefix("- ")
        for line in eval_input.splitlines()
        if line.strip().startswith("- ")
    }

    assert choices == {*COMPONENT_NAMES, "all"}


@pytest.mark.parametrize("component", COMPONENT_NAMES)
def test_builds_fresh_config_for_every_component(component):
    first = build_component_config(component, judge_llm=object())
    second = build_component_config(component, judge_llm=object())

    assert first is not second
    assert first.evaluators is not second.evaluators
    assert all(
        left is not right
        for left, right in zip(first.evaluators, second.evaluators, strict=True)
    )


def test_builds_fresh_generation_config_with_bound_judge():
    judge_llm = object()

    config = build_component_config("generation", judge_llm=judge_llm)

    assert [type(evaluator) for evaluator in config.evaluators] == [
        GroundednessEvaluator,
        CoverageEvaluator,
        TitleSpecificityEvaluator,
        RedundancyEvaluator,
    ]
    assert all(evaluator.llm is judge_llm for evaluator in config.evaluators[:3])


def test_builds_expected_non_generation_evaluators():
    judge_llm = object()

    condensation_config = build_component_config("condensation", judge_llm=judge_llm)
    refinement_config = build_component_config("refinement", judge_llm=judge_llm)
    mapping_config = build_component_config("mapping", judge_llm=judge_llm)

    assert [type(evaluator) for evaluator in condensation_config.evaluators] == [
        CondensationQualityEvaluator,
        RedundancyEvaluator,
    ]
    assert condensation_config.evaluators[0].llm is judge_llm
    assert [type(evaluator) for evaluator in refinement_config.evaluators] == [
        RefinementQualityEvaluator
    ]
    assert refinement_config.evaluators[0].llm is judge_llm
    assert [type(evaluator) for evaluator in mapping_config.evaluators] == [
        MappingMetricsEvaluator
    ]


def test_mapping_question_filter_is_exact_and_per_config():
    filtered = build_component_config("mapping", judge_llm=object(), question_num=1)
    unfiltered = build_component_config("mapping", judge_llm=object())
    question_1 = Case("one", {}, None, {"question_part": "question_part_1"})
    question_10 = Case("ten", {}, None, {"question_part": "question_part_10"})

    assert filtered.case_filter is not None
    assert filtered.case_filter(question_1) is True
    assert filtered.case_filter(question_10) is False
    assert unfiltered.case_filter is None


@pytest.mark.parametrize("component", ["generation", "condensation", "refinement"])
def test_rejects_mapping_question_filter_for_other_components(component):
    with pytest.raises(ValueError, match="only supported for the mapping"):
        build_component_config(component, judge_llm=object(), question_num=1)


def test_rejects_invalid_question_number():
    with pytest.raises(ValueError, match="greater than zero"):
        build_component_config("mapping", judge_llm=object(), question_num=0)


async def test_generation_task_runs_full_pipeline_and_normalises_output(monkeypatch):
    llm = object()
    calls = []

    async def fake_generation(*, responses_df, llm, question):
        calls.append(("generation", responses_df.to_dict("records"), llm, question))
        return pd.DataFrame([{"topic": "Initial"}]), None

    async def fake_condensation(themes_df, *, llm, question):
        calls.append(("condensation", themes_df.to_dict("records"), llm, question))
        return pd.DataFrame([{"topic": "Condensed"}]), None

    async def fake_refinement(themes_df, *, llm, question):
        calls.append(("refinement", themes_df.to_dict("records"), llm, question))
        return pd.DataFrame([{"topic_id": "A", "topic": "Label: Description"}]), None

    monkeypatch.setattr(generation, "theme_generation", fake_generation)
    monkeypatch.setattr(generation, "theme_condensation", fake_condensation)
    monkeypatch.setattr(generation, "theme_refinement", fake_refinement)

    output = await generation.run_generation_task(
        {
            "question": "Question?",
            "responses": [{"response_id": "1", "response": "Answer"}],
        },
        llm,
    )

    assert [call[0] for call in calls] == ["generation", "condensation", "refinement"]
    assert all(call[2] is llm for call in calls)
    assert output == {
        "themes": [
            {
                "topic_id": "A",
                "topic": "Label: Description",
                "topic_label": "Label",
                "topic_description": "Description",
            }
        ]
    }


async def test_condensation_task_uses_common_output_schema(monkeypatch):
    async def fake_condensation(themes_df, *, llm, question):
        assert themes_df.to_dict("records") == [{"topic": "Original"}]
        assert question == "Question?"
        return pd.DataFrame([{"topic": "Condensed"}]), None

    monkeypatch.setattr(condensation, "theme_condensation", fake_condensation)

    output = await condensation.run_condensation_task(
        {"question": "Question?", "themes": [{"topic": "Original"}]}, object()
    )

    assert output == {"themes": [{"topic": "Condensed"}]}


async def test_refinement_task_uses_common_output_schema(monkeypatch):
    async def fake_refinement(themes_df, *, llm, question):
        assert themes_df.to_dict("records") == [{"topic": "Original"}]
        assert question == "Question?"
        return pd.DataFrame([{"topic": "Refined"}]), None

    monkeypatch.setattr(refinement, "theme_refinement", fake_refinement)

    output = await refinement.run_refinement_task(
        {"question": "Question?", "themes": [{"topic": "Original"}]}, object()
    )

    assert output == {"themes": [{"topic": "Refined"}]}


async def test_mapping_task_returns_labels_and_reports_unprocessable(
    monkeypatch, caplog
):
    llm = object()

    async def fake_mapping(*, responses_df, llm, question, refined_themes_df):
        assert responses_df.to_dict("records") == [
            {"response_id": 7, "response": "Answer"}
        ]
        assert refined_themes_df.to_dict("records") == [
            {"topic_id": "A", "topic": "Theme"}
        ]
        assert question == "Question?"
        return (
            pd.DataFrame([{"response_id": 7, "labels": ["A"]}]),
            pd.DataFrame([{"response_id": 8}]),
        )

    monkeypatch.setattr(mapping, "theme_mapping", fake_mapping)

    output = await mapping.run_mapping_task(
        {
            "question": "Question?",
            "responses": [{"response_id": 7, "response": "Answer"}],
            "topics": [{"topic_id": "A", "topic": "Theme"}],
        },
        llm,
    )

    assert output == {"labels": {"7": ["A"]}}
    assert "1 responses could not be processed" in caplog.text
