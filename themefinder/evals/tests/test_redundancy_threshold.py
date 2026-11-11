"""Tests for the redundancy threshold review script."""

import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pytest

from scripts import redundancy_threshold
from scripts.redundancy_threshold import Theme, ThemeVariants

SOURCES = [
    {
        "topic_id": "A",
        "topic_label": "Complete ban support",
        "topic_description": "Ban it.",
    },
    {
        "topic_id": "B",
        "topic_label": "Economic impact concerns",
        "topic_description": "Jobs.",
    },
]


class _VariantWriter:
    """An LLM double that names each variant after the source and the kind."""

    def __init__(self):
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str, output_model=None):
        self.prompts.append(prompt)
        source = (
            "A" if "Complete ban support" in prompt.split("Other themes")[0] else "B"
        )
        variants = {
            kind: Theme(topic_label=f"{source} {kind}", topic_description=kind)
            for kind in (
                *redundancy_threshold.REDUNDANT_KINDS,
                redundancy_threshold.DISTINCT_KIND,
            )
        }
        return SimpleNamespace(parsed=ThemeVariants(**variants))


async def test_build_items_groups_variants_with_their_source_and_isolates_the_distinct_one():
    llm = _VariantWriter()

    themes = await redundancy_threshold.build_items(SOURCES, llm)

    by_id = {theme["topic_id"]: theme for theme in themes}
    assert len(themes) == 2 + 2 * 4
    assert by_id["A"]["group"] == "A" and by_id["A"]["kind"] == "source"
    assert by_id["A.rewording"]["group"] == "A"
    assert by_id["A.narrower"]["group"] == "A"
    assert by_id["A.hard_negative"]["group"] == "A.hard_negative"
    assert by_id["B.reframing"]["group"] == "B"
    assert any("- Economic impact concerns" in prompt for prompt in llm.prompts)


def test_redundant_pairs_are_exactly_the_same_group_pairs():
    themes = [
        {"topic_id": "A", "group": "A"},
        {"topic_id": "A.rewording", "group": "A"},
        {"topic_id": "A.hard_negative", "group": "A.hard_negative"},
        {"topic_id": "B", "group": "B"},
    ]

    assert redundancy_threshold.redundant_pairs(themes) == [["A", "A.rewording"]]


def test_publish_upserts_one_item_per_question_part_with_stable_ids():
    client = Mock()
    client.get_dataset.side_effect = Exception("not found")
    themes = [
        {"topic_id": "A", "group": "A"},
        {"topic_id": "A.rewording", "group": "A"},
    ]

    redundancy_threshold.publish_items(
        client, "demo", {"question_part_1": themes}, model="judge"
    )

    name = "eval/redundancy_threshold/demo"
    client.create_dataset.assert_called_once()
    assert client.create_dataset.call_args.kwargs["name"] == name
    item = client.create_dataset_item.call_args.kwargs
    assert item["id"] == str(uuid5(NAMESPACE_URL, f"{name}:question_part_1"))
    assert item["dataset_name"] == name
    assert item["expected_output"] == {"redundant_pairs": [["A", "A.rewording"]]}
    assert item["metadata"] == {
        "dataset": "demo",
        "question_part": "question_part_1",
        "model": "judge",
    }
    client.flush.assert_called_once()


def test_thresholds_are_inclusive_of_both_ends():
    assert redundancy_threshold.thresholds(0.5, 0.95, 0.05) == [
        0.5,
        0.55,
        0.6,
        0.65,
        0.7,
        0.75,
        0.8,
        0.85,
        0.9,
        0.95,
    ]


def test_score_threshold_counts_pairs_at_or_above_the_threshold():
    pairs = [(0.95, True), (0.80, True), (0.86, False), (0.30, False)]

    scored = redundancy_threshold.score_threshold(pairs, 0.85)

    assert scored == {
        "threshold": 0.85,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "true_positives": 1,
        "false_positives": 1,
        "false_negatives": 1,
    }


def test_labelled_pairs_can_leave_a_variant_kind_out():
    themes = [
        {"topic_id": "A", "group": "A", "kind": "source"},
        {"topic_id": "A.narrower", "group": "A", "kind": "narrower"},
        {"topic_id": "B", "group": "B", "kind": "source"},
    ]
    similarity = np.array([[1.0, 0.9, 0.2], [0.9, 1.0, 0.1], [0.2, 0.1, 1.0]])

    assert redundancy_threshold.labelled_pairs(themes, similarity) == [
        (0.9, True),
        (0.2, False),
        (0.1, False),
    ]
    assert redundancy_threshold.labelled_pairs(themes, similarity, ("narrower",)) == [
        (0.2, False)
    ]


def test_sweep_reads_local_items_and_writes_a_csv(monkeypatch, tmp_path, capsys):
    themes = [
        {
            "topic_id": "A",
            "topic_label": "a",
            "topic_description": "",
            "group": "A",
            "kind": "source",
        },
        {
            "topic_id": "A.rewording",
            "topic_label": "a2",
            "topic_description": "",
            "group": "A",
            "kind": "rewording",
        },
        {
            "topic_id": "B",
            "topic_label": "b",
            "topic_description": "",
            "group": "B",
            "kind": "source",
        },
    ]
    local = tmp_path / "data" / "demo"
    local.mkdir(parents=True)
    (local / "question_part_1.json").write_text(
        json.dumps({"themes": themes, "model": "judge"})
    )
    monkeypatch.setattr(redundancy_threshold, "LOCAL_DIR", tmp_path / "data")
    monkeypatch.setattr(redundancy_threshold, "SWEEP_DIR", tmp_path / "runs")
    vectors = {"a": [1.0, 0.0], "a2": [0.95, 0.312], "b": [0.0, 1.0]}
    model = SimpleNamespace(
        encode=lambda texts, **_: np.array([vectors[text] for text in texts])
    )
    monkeypatch.setattr(redundancy_threshold, "get_sentence_model", lambda: model)
    args = redundancy_threshold._parse_args(
        [
            "sweep",
            "--dataset",
            "demo",
            "--source",
            "local",
            "--start",
            "0.9",
            "--stop",
            "0.97",
            "--step",
            "0.07",
        ]
    )

    rows = redundancy_threshold.sweep(args)

    assert [row["threshold"] for row in rows] == [0.9, 0.97]
    assert rows[0]["f1"] == 1.0 and rows[1]["f1"] == 0.0
    written = (tmp_path / "runs" / "demo" / "sweep_title.csv").read_text().splitlines()
    assert written[0].startswith("threshold,precision,recall,f1")
    assert len(written) == 3
    assert "Best F1 1.000 at threshold 0.9;" in capsys.readouterr().out


def test_publish_command_reuses_the_saved_items_and_their_model(monkeypatch, tmp_path):
    local = tmp_path / "demo"
    local.mkdir()
    themes = [{"topic_id": "A", "group": "A"}]
    (local / "question_part_1.json").write_text(
        json.dumps({"themes": themes, "model": "judge"})
    )
    monkeypatch.setattr(redundancy_threshold, "LOCAL_DIR", tmp_path)
    monkeypatch.setattr(redundancy_threshold, "get_langfuse_client", lambda: "client")
    published = Mock()
    monkeypatch.setattr(redundancy_threshold, "publish_items", published)

    redundancy_threshold.main(["publish", "--dataset", "demo"])

    published.assert_called_once_with(
        "client", "demo", {"question_part_1": themes}, "judge"
    )


def test_thresholds_never_pass_the_stop_value():
    assert redundancy_threshold.thresholds(0.5, 0.98, 0.05)[-1] == 0.95
    assert redundancy_threshold.thresholds(0.7, 0.7, 0.05) == [0.7]


@pytest.mark.parametrize(
    "argv",
    [["sweep", "--step", "0"], ["sweep", "--start", "0.9", "--stop", "0.5"]],
    ids=["zero-step", "stop-below-start"],
)
def test_sweep_rejects_an_empty_threshold_range(argv):
    with pytest.raises(SystemExit):
        redundancy_threshold._parse_args(argv)


def test_build_needs_a_model():
    with pytest.raises(SystemExit):
        redundancy_threshold._parse_args(["build", "--model", ""])
