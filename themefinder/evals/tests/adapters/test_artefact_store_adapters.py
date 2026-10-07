"""Offline tests for artefact store ports and adapters."""

from __future__ import annotations

import json
from abc import ABC

import pytest
from httpx import RequestError
from langfuse.api.core import ApiError

from adapters.artefact_stores.base import ArtefactStorePort
from adapters.artefact_stores.langfuse_adapter import LangfuseArtefactStore
from adapters.artefact_stores.local_json_adapter import LocalJSONArtefactStore
from eval_types import Case, CaseOutcome, RunReport, Score
from fakes import FakeLangfuseClient, FakeTrace
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
        context = LangfuseContext(client=FakeLangfuseClient())
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
    def test_record_case_creates_span_and_links_dataset_item(self):
        client = FakeLangfuseClient()
        context = LangfuseContext(
            client=client,
            session_id="session-v3",
            tags=["eval", "generation"],
            metadata={"dataset": "demo"},
        )
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(
            case=_make_case(
                case_id="case-v3",
                question_part="question_part_3",
                langfuse_item_id="item-v3",
            ),
            scores=[Score("coverage", 4.0, "linked")],
        )

        store.start_run("generation", "demo")
        store.record_case(outcome)

        assert client.create_trace_id_calls == 1
        assert client.start_span_calls == [
            {
                "trace_context": {"trace_id": "generated-trace-id"},
                "name": "session-v3:question_part_3",
                "input": {"question": "What changed?"},
                "output": {"themes": {"A": "desc"}},
                "metadata": {"dataset": "demo"},
                "level": "DEFAULT",
                "status_message": None,
            }
        ]
        request = client.api.dataset_run_items.create_calls[0]
        assert request.run_name == "session-v3"
        assert request.dataset_item_id == "item-v3"
        assert request.trace_id == "generated-trace-id"
        assert request.metadata == {"dataset": "demo"}
        assert client.last_span_trace.trace_updates == [
            {
                "input": {"question": "What changed?"},
                "output": {"themes": {"A": "desc"}},
                "metadata": {"dataset": "demo"},
                "tags": ["eval", "generation"],
                "session_id": "session-v3",
            }
        ]
        assert client.scores == [
            {
                "comment": "linked",
                "data_type": "NUMERIC",
                "name": "coverage",
                "trace_id": "generated-trace-id",
                "value": 4.0,
            }
        ]

    @pytest.mark.parametrize(
        "link_error",
        [
            ApiError(status_code=503, body={"message": "unavailable"}),
            RequestError("network unavailable"),
        ],
        ids=["api-error", "network-error"],
    )
    def test_link_failure_still_records_trace_and_scores(self, caplog, link_error):
        client = FakeLangfuseClient()
        client.api.dataset_run_items.error = link_error
        context = LangfuseContext(client=client, session_id="session-v3")
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(
            case=_make_case(langfuse_item_id="item-v3"),
            scores=[Score("coverage", 4.0)],
        )

        store.start_run("generation", "demo")
        store.record_case(outcome)

        assert len(client.api.dataset_run_items.create_calls) == 1
        assert client.scores == [
            {
                "data_type": "NUMERIC",
                "name": "coverage",
                "trace_id": "generated-trace-id",
                "value": 4.0,
            }
        ]
        assert "recording an unlinked trace instead" in caplog.text

    def test_record_case_without_langfuse_item_id_still_records_scores(self):
        client = FakeLangfuseClient()
        context = LangfuseContext(client=client, session_id="session-2")
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(case=_make_case(question_part="question_part_3"))

        store.start_run("generation", "demo")
        store.record_case(outcome)

        assert client.start_span_calls[0]["name"] == "session-2:question_part_3"
        assert client.scores[0]["trace_id"] == "generated-trace-id"
        assert client.scores[0]["name"] == "groundedness"

    def test_record_case_forwards_score_comments(self):
        client = FakeLangfuseClient()
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
                "trace_id": "generated-trace-id",
                "value": 1.2,
            }
        ]

    def test_record_case_propagates_score_creation_errors(self):
        client = FakeLangfuseClient()
        client.raise_on_create_score = RuntimeError("boom")
        context = LangfuseContext(client=client, session_id="session-1")
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(
            case=_make_case(case_id="case-9", question_part="question_part_9")
        )

        store.start_run("generation", "demo")

        with pytest.raises(RuntimeError, match="boom"):
            store.record_case(outcome)

        assert client.span_exit_calls == [(RuntimeError, "boom")]

    def test_record_case_logs_trace_update_failures(self, monkeypatch, caplog):
        client = FakeLangfuseClient()
        context = LangfuseContext(client=client, session_id="session-1")
        store = LangfuseArtefactStore(context=context, owns_context=False)
        outcome = _make_outcome(case=_make_case(langfuse_item_id="item-123"))

        def raise_on_update_trace(self, **kwargs):
            raise RuntimeError("trace update failed")

        monkeypatch.setattr(FakeTrace, "update_trace", raise_on_update_trace)
        store.start_run("generation", "demo")

        with pytest.raises(RuntimeError, match="trace update failed"):
            store.record_case(outcome)

        assert client.span_exit_calls == [(RuntimeError, "trace update failed")]
        assert client.scores == []
        assert (
            "Failed to update Langfuse trace for case case-1 and run session-1: "
            "trace update failed" in caplog.text
        )

    def test_finish_run_flushes_when_context_is_owned(self):
        client = FakeLangfuseClient()
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
        client = FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=False)

        store.start_run("generation", "demo")
        store.finish_run(RunReport(outcomes=[_make_outcome()]))

        assert client.flush_calls == 0

    def test_finish_run_ignores_non_pydantic_engine_report_safely(self):
        client = FakeLangfuseClient()
        context = LangfuseContext(client=client)
        store = LangfuseArtefactStore(context=context, owns_context=False)

        store.start_run("generation", "demo")
        results = store.finish_run(
            RunReport(outcomes=[_make_outcome()]), engine_report=object()
        )

        assert client.flush_calls == 0
        assert results["question_part_1_groundedness"] == 4.5
