"""Langfuse artefact store implementation."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from eval_types import CaseOutcome, RunReport
from httpx import RequestError
from utils import langfuse as langfuse_utils
from utils.langfuse import LangfuseContext
from utils.logging_config import get_logger

from .base import ArtefactStorePort, case_key, flatten_run_report, json_safe

logger = get_logger(__name__)


class LangfuseArtefactStore(ArtefactStorePort):
    def __init__(self, context: LangfuseContext, owns_context: bool):
        self.context = context
        self.owns_context = owns_context
        self._component: str | None = None
        self._dataset: str | None = None

    def start_run(self, component: str, dataset: str) -> None:
        self._component = component
        self._dataset = dataset

    def record_case(self, outcome: CaseOutcome) -> None:
        if not self.context.client:
            return

        with self._trace_for_outcome(outcome) as (trace, trace_id):
            if trace is not None:
                self._update_trace(trace, output=outcome.output)

            if not trace_id:
                logger.warning(
                    "Skipping score persistence for %s because no Langfuse trace id was created",
                    outcome.case.id,
                )
                return

            for score in outcome.scores:
                score_kwargs: dict[str, Any] = {
                    "trace_id": trace_id,
                    "name": score.name,
                    "value": score.value,
                    "data_type": "NUMERIC",
                }
                if score.comment:
                    score_kwargs["comment"] = score.comment
                self.context.client.create_score(**score_kwargs)

    def finish_run(
        self,
        report: RunReport,
        *,
        engine_report: Any | None = None,
    ) -> dict[str, Any]:
        native_report = (
            engine_report if engine_report is not None else report.engine_report
        )
        if self._is_pydantic_evals_report(native_report):
            printer = getattr(native_report, "print", None)
            if callable(printer):
                printer()

        if self.owns_context:
            langfuse_utils.flush(self.context)

        return flatten_run_report(report)

    @contextmanager
    def _trace_for_outcome(
        self,
        outcome: CaseOutcome,
    ) -> Generator[tuple[Any, str | None], None, None]:
        dataset_item_id = outcome.case.metadata.get("langfuse_item_id")
        client = self.context.client
        if client is None:
            yield None, None
            return

        inputs = json_safe(outcome.case.inputs)
        outputs = json_safe(outcome.output)
        trace_id = client.create_trace_id()
        trace_name = f"{self._run_name}:{case_key(outcome.case)}"
        trace_status = outcome.error
        with client.start_as_current_span(
            trace_context={"trace_id": trace_id},
            name=trace_name,
            input=inputs,
            output=outputs,
            metadata=self.context.metadata,
            level="ERROR" if trace_status is not None else "DEFAULT",
            status_message=trace_status,
        ) as trace:
            try:
                trace.update_trace(
                    input=inputs,
                    output=outputs,
                    metadata=self.context.metadata,
                    tags=self.context.tags,
                    session_id=self.context.session_id,
                )
            except BaseException as exc:
                logger.error(
                    "Failed to update Langfuse trace for case %s and run %s: %s",
                    outcome.case.id,
                    self._run_name,
                    exc,
                )
                raise

            if dataset_item_id:
                self._link_dataset_item_to_trace(
                    client=client,
                    dataset_item_id=str(dataset_item_id),
                    trace_id=trace.trace_id,
                    case_id=outcome.case.id,
                )
            yield trace, trace.trace_id

    def _link_dataset_item_to_trace(
        self,
        *,
        client: Any,
        dataset_item_id: str,
        trace_id: str,
        case_id: str,
    ) -> None:
        from langfuse.api import CreateDatasetRunItemRequest
        from langfuse.api.core import ApiError

        try:
            client.api.dataset_run_items.create(
                request=CreateDatasetRunItemRequest(
                    runName=self._run_name,
                    datasetItemId=dataset_item_id,
                    traceId=trace_id,
                    metadata=self.context.metadata,
                )
            )
        except (ApiError, RequestError) as exc:
            logger.warning(
                "Failed to link Langfuse dataset item %s for case %s: %s; "
                "recording an unlinked trace instead",
                dataset_item_id,
                case_id,
                exc,
            )

    def _update_trace(self, trace: Any, *, output: Any) -> None:
        update = getattr(trace, "update", None)
        if callable(update):
            update(output=json_safe(output))

    @property
    def _run_name(self) -> str:
        if self.context.session_id:
            return self.context.session_id

        component = self._component or "unknown-component"
        dataset = self._dataset or "unknown-dataset"
        return f"{component}:{dataset}"

    @staticmethod
    def _is_pydantic_evals_report(engine_report: Any) -> bool:
        if engine_report is None:
            return False

        try:
            from pydantic_evals.reporting import EvaluationReport
        except ImportError:
            return False

        return isinstance(engine_report, EvaluationReport)
