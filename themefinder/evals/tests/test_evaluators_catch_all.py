from unittest.mock import AsyncMock

import pytest
from evaluators import (
    _calculate_coverage_scores,
    _calculate_groundedness_scores,
    _without_catch_all_themes,
)

THEMES = [
    {"topic_id": "A", "topic_label": "Complete Ban Support", "topic": "A: x"},
    {"topic_id": "XX", "topic_label": "None of the Above", "topic": "XX: y"},
    {"topic_id": "XY", "topic_label": "No Reason Given", "topic": "XY: z"},
]


def test_catch_all_themes_are_removed_from_a_list():
    result = _without_catch_all_themes(THEMES)

    assert [t["topic_id"] for t in result] == ["A"]


def test_catch_all_themes_are_matched_by_label_when_ids_differ():
    themes = [
        {"topic_id": "M", "topic_label": " none of the above "},
        {"topic_id": "N", "topic_label": "Real Theme"},
    ]

    assert [t["topic_id"] for t in _without_catch_all_themes(themes)] == ["N"]


def test_catch_all_themes_are_removed_from_a_dict_keyed_by_label():
    themes = {"Real Theme": "a", "No Reason Given": "b"}

    assert _without_catch_all_themes(themes) == {"Real Theme": "a"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "calculate", [_calculate_coverage_scores, _calculate_groundedness_scores]
)
async def test_judge_prompt_never_sees_catch_all_themes(monkeypatch, calculate):
    captured = {}

    def fake_prompt(topic_list_1, topic_list_2):
        captured["prompt_lists"] = [topic_list_1, topic_list_2]
        return "prompt"

    monkeypatch.setattr("evaluators.generation_eval_prompt", fake_prompt)
    monkeypatch.setattr(
        "evaluators._parse_evaluation_response", lambda content: {"average": 5}
    )
    llm = AsyncMock()
    generated = [{"topic_id": "A", "topic_label": "Generated"}]

    await calculate(generated, THEMES, llm)

    labels = [t["topic_label"] for lst in captured["prompt_lists"] for t in lst]
    assert "None of the Above" not in labels
    assert "No Reason Given" not in labels
    assert "Complete Ban Support" in labels
