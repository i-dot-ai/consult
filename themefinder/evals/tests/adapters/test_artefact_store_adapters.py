"""Offline tests for artefact store ports and adapters."""

from __future__ import annotations

import json
from abc import ABC
from contextlib import contextmanager

import pytest
from adapters.artefact_stores.base import ArtefactStorePort
from adapters.artefact_stores.langfuse_adapter import LangfuseArtefactStore
from adapters.artefact_stores.local_json_adapter import LocalJSONArtefactStore
from eval_types import Case, CaseOutcome, RunReport, Score
from utils.langfuse import LangfuseContext


def _make_case(
    *,
    case_id: str = "case-1",
    question_part: str | None = None,
    langfuse_item_id: str | None = None,
) -> Case:
    metadata = {}
    if question_part is not None:
        metadata["question_part"] = question_part
    if langfuse_item_id is not None:
        metadata["langfuse_item_id"] = langfuse_item_id

    return Case(
        id=case_id,
        inputs={"question": "What changed?"},
        expected_output={"themes": {"A": "desc"}},
        metadata=metadata,
    )


def _make_outcome(
    *,
    case: Case | None = None,
    output: dict | None = None,
    scores: list[Score] | None = None,
    error: str | None = None,
) -> CaseOutcome:
    return CaseOutcome(
        case=case or _make_case(question_part="question_part_1"),
        output=output or {"themes": {"A": "desc"}},
        scores=scores or [Score("groundedness", 4.5, "solid")],
        error=error,
    )


class TestArtefactStorePortContract:
    def test_local_json_adapter_is_artefact_store_port(self, tmp_path):
        assert isinstance(
            LocalJSONArtefactStore(output_dir=tmp_path), ArtefactStorePort
        )

    def test_langfuse_adapter_is_artefact_store_port(self):
        context = LangfuseContext(client=_FakeLangfuseClient())
        assert isinstance(
            LangfuseArtefactStore(context=context, owns_context=False),
            ArtefactStorePort,
        )

    def test_incomplete_subclass_cannot_be_instantiated(self):
        class _IncompleteArtefactStore(ArtefactStorePort, ABC):
            def start_run(self, component: str, dataset: str) -> None:
                return None

        with pytest.raises(TypeError):
            _IncompleteArtefactStore()


class TestLocalJSONArtefactStore:
    def test_writes_results_to_component_dataset_path(self, tmp_path):
        store = LocalJSONArtefactStore(output_dir=tmp_path)
        outcome = _make_outcome(
            case=_make_case(question_part="question_part_2"),
            output={"labels": {"r1": ["A"]}},
            scores=[Score("f1_score", 0.75, "three of four")],
            error="row-7 missing field",
        )
        report = RunReport(outcomes=[outcome])

        store.start_run("mapping", "demo_dataset")
        store.record_case(outcome)
        results = store.finish_run(report)

        target = tmp_path / "mapping" / "demo_dataset" / "results.json"
        assert target.exists()
        payload = json.loads(target.read_text(encoding="utf-8"))

        assert payload["component"] == "mapping"
        assert payload["dataset"] == "demo_dataset"
        assert payload["results"] == {
            "question_part_2_f1_score": 0.75,
            "question_part_2_output": {"labels": {"r1": ["A"]}},
        }
        assert payload["errors"] == {"question_part_2": "row-7 missing field"}
        assert payload["outcomes"] == [
            {
                "case": {
                    "expected_output": {"themes": {"A": "desc"}},
                    "id": "case-1",
                    "inputs": {"question": "What changed?"},
                    "metadata": {"question_part": "question_part_2"},
                },
                "error": "row-7 missing field",
                "output": {"labels": {"r1": ["A"]}},
                "scores": [
                    {
                        "comment": "three of four",
                        "name": "f1_score",
                        "value": 0.75,
                    }
                ],
            }
        ]
        assert results == payload["results"]

    def test_subsequent_runs_overwrite_existing_results(self, tmp_path):
        store = LocalJSONArtefactStore(output_dir=tmp_path)

        first = _make_outcome(
            case=_make_case(question_part="question_part_1"),
            output={"themes": {"A": "first"}},
            scores=[Score("coverage", 1.0, "first run")],
        )
        second = _make_outcome(
            case=_make_case(question_part="question_part_1"),
            output={"themes": {"B": "second"}},
            scores=[Score("coverage", 2.0, "second run")],
        )

        store.start_run("generation", "dataset_x")
        store.record_case(first)
        store.finish_run(RunReport(outcomes=[first]))

        store.start_run("generation", "dataset_x")
        store.record_case(second)
        store.finish_run(RunReport(outcomes=[second]))

        payload = json.loads(
            (tmp_path / "generation" / "dataset_x" / "results.json").read_text(
                encoding="utf-8"
            )
        )
        assert payload["results"] == {
            "question_part_1_coverage": 2.0,
            "question_part_1_output": {"themes": {"B": "second"}},
        }
        assert payload["outcomes"][0]["scores"][0]["comment"] == "second run"


class TestLangfuseArtefactStore:
    def test_record_case_with_langfuse_item_id_creates_trace_linked_scores(self):
        client = _FakeLangfuseClient()
        client.dataset_items["item-123"] = _FakeDatasetItem("item-123")
        context = LangfuseContext(
            client=client,
            session_id="session-1",
            tags=["eval", "generation"],
            metadata={"dataset": "demo"},
        )
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(
            case=_make_case(
                case_id="case-9",
                question_part="question_part_9",
                langfuse_item_id="item-123",
            ),
            scores=[Score("coverage", 3.2, "kept comment")],
        )

        store.start_run("generation", "demo")
        store.record_case(outcome)

        dataset_item = client.dataset_items["item-123"]
        assert dataset_item.run_calls == [
            {"run_name": "session-1", "run_metadata": {"dataset": "demo"}}
        ]
        assert client.create_trace_calls == []
        assert client.scores == [
            {
                "comment": "kept comment",
                "data_type": "NUMERIC",
                "name": "coverage",
                "trace_id": "dataset-trace-item-123",
                "value": 3.2,
            }
        ]
        assert dataset_item.last_trace.updated_output == {"themes": {"A": "desc"}}
        assert dataset_item.last_trace.trace_updates == [
            {
                "metadata": {"dataset": "demo"},
                "session_id": "session-1",
                "tags": ["eval", "generation"],
            }
        ]

    def test_record_case_without_langfuse_item_id_still_records_scores(self):
        client = _FakeLangfuseClient()
        context = LangfuseContext(client=client, session_id="session-2")
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(case=_make_case(question_part="question_part_3"))

        store.start_run("generation", "demo")
        store.record_case(outcome)

        assert len(client.create_trace_calls) == 1
        assert client.create_trace_calls[0]["name"] == "session-2:question_part_3"
        assert client.scores[0]["trace_id"] == "trace-1"
        assert client.scores[0]["name"] == "groundedness"

    def test_record_case_forwards_score_comments(self):
        client = _FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(
            scores=[Score("specificity", 1.2, "comment from evaluator")]
        )

        store.start_run("generation", "demo")
        store.record_case(outcome)

        assert client.scores == [
            {
                "comment": "comment from evaluator",
                "data_type": "NUMERIC",
                "name": "specificity",
                "trace_id": "trace-1",
                "value": 1.2,
            }
        ]

    def test_finish_run_flushes_when_context_is_owned(self):
        client = _FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=True)
        outcome = _make_outcome()
        report = RunReport(outcomes=[outcome])

        store.start_run("generation", "demo")
        results = store.finish_run(report)

        assert client.flush_calls == 1
        assert results == {
            "question_part_1_groundedness": 4.5,
            "question_part_1_output": {"themes": {"A": "desc"}},
        }

    def test_finish_run_does_not_flush_when_context_is_not_owned(self):
        client = _FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=False)

        store.start_run("generation", "demo")
        store.finish_run(RunReport(outcomes=[_make_outcome()]))

        assert client.flush_calls == 0

    def test_finish_run_ignores_non_pydantic_engine_report_safely(self):
        client = _FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=False)

        store.start_run("generation", "demo")
        results = store.finish_run(
            RunReport(outcomes=[_make_outcome()]), engine_report=object()
        )

        assert client.flush_calls == 0
        assert results["question_part_1_groundedness"] == 4.5


class _FakeTrace:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.updated_output = None
        self.trace_updates: list[dict] = []

    def update(self, *, output):
        self.updated_output = output

    def update_trace(self, *, session_id=None, tags=None, metadata=None):
        self.trace_updates.append(
            {
                "session_id": session_id,
                "tags": tags,
                "metadata": metadata,
            }
        )


class _FakeDatasetItem:
    def __init__(self, item_id: str):
        self.item_id = item_id
        self.run_calls: list[dict] = []
        self.last_trace: _FakeTrace | None = None

    @contextmanager
    def run(self, *, run_name: str, run_metadata: dict | None = None):
        self.run_calls.append({"run_name": run_name, "run_metadata": run_metadata})
        trace = _FakeTrace(f"dataset-trace-{self.item_id}")
        self.last_trace = trace
        yield trace


class _FakeLangfuseClient:
    def __init__(self):
        self.dataset_items: dict[str, _FakeDatasetItem] = {}
        self.create_trace_calls: list[dict] = []
        self.scores: list[dict] = []
        self.flush_calls = 0

    def get_dataset_item(self, item_id: str):
        return self.dataset_items.get(item_id)

    def create_trace(self, **kwargs):
        self.create_trace_calls.append(kwargs)
        return _FakeTrace(f"trace-{len(self.create_trace_calls)}")

    def create_score(self, **kwargs):
        self.scores.append(kwargs)

    def flush(self):
        self.flush_calls += 1
