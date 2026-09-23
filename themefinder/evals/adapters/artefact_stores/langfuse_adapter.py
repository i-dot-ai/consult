"""Langfuse artefact store implementation."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

from eval_types import CaseOutcome, RunReport
from utils import langfuse as langfuse_utils
from utils.langfuse import LangfuseContext

from .base import ArtefactStorePort, case_key, flatten_run_report, json_safe

logger = logging.getLogger(__name__)


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
        if dataset_item_id:
            with self._dataset_item_trace(outcome, str(dataset_item_id)) as trace_data:
                yield trace_data
                return

        yield self._create_unlinked_trace(outcome)

    @contextmanager
    def _dataset_item_trace(
        self,
        outcome: CaseOutcome,
        dataset_item_id: str,
    ) -> Generator[tuple[Any, str | None], None, None]:
        dataset_item = self._get_dataset_item(dataset_item_id)
        if dataset_item is None or not hasattr(dataset_item, "run"):
            logger.warning(
                "Langfuse dataset item %s was not available for case %s; "
                "creating an unlinked trace instead",
                dataset_item_id,
                outcome.case.id,
            )
            yield self._create_unlinked_trace(outcome)
            return

        try:
            run_cm = dataset_item.run(
                run_name=self._run_name,
                run_metadata=self.context.metadata,
            )
            trace = run_cm.__enter__()
        except Exception as exc:
            logger.warning(
                "Failed to create Langfuse dataset-item trace for %s: %s",
                outcome.case.id,
                exc,
            )
            yield self._create_unlinked_trace(outcome)
            return

        update_trace = getattr(trace, "update_trace", None)
        if callable(update_trace):
            update_trace(
                session_id=self.context.session_id,
                tags=self.context.tags,
                metadata=self.context.metadata,
            )

        try:
            yield trace, self._trace_id(trace)
        except BaseException as exc:
            suppress = run_cm.__exit__(type(exc), exc, exc.__traceback__)
            if not suppress:
                raise
        else:
            run_cm.__exit__(None, None, None)

    def _create_unlinked_trace(self, outcome: CaseOutcome) -> tuple[Any, str | None]:
        if not self.context.client:
            return None, None

        trace_kwargs = {
            "name": f"{self._run_name}:{case_key(outcome.case)}",
            "input": json_safe(outcome.case.inputs),
            "output": json_safe(outcome.output),
            "metadata": self.context.metadata,
            "tags": self.context.tags,
            "session_id": self.context.session_id,
        }

        create_trace = getattr(self.context.client, "create_trace", None)
        if callable(create_trace):
            trace = create_trace(**trace_kwargs)
            return trace, self._trace_id(trace)

        trace_factory = getattr(self.context.client, "trace", None)
        if callable(trace_factory):
            trace = trace_factory(**trace_kwargs)
            self._update_trace(trace, output=outcome.output)
            return trace, self._trace_id(trace)

        logger.warning("Langfuse client does not expose a trace creation method")
        return None, None

    def _get_dataset_item(self, dataset_item_id: str) -> Any | None:
        if not self.context.client:
            return None

        getter = getattr(self.context.client, "get_dataset_item", None)
        if callable(getter):
            return getter(dataset_item_id)

        api = getattr(self.context.client, "api", None)
        if api is not None:
            dataset_item_api = getattr(api, "dataset_item", None)
            get_method = getattr(dataset_item_api, "get", None)
            if callable(get_method):
                return get_method(dataset_item_id)

        return None

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
    def _trace_id(trace: Any) -> str | None:
        if trace is None:
            return None
        return getattr(trace, "trace_id", None) or getattr(trace, "id", None)

    @staticmethod
    def _is_pydantic_evals_report(engine_report: Any) -> bool:
        if engine_report is None:
            return False

        try:
            from pydantic_evals.reporting import EvaluationReport
        except ImportError:
            return False

        return isinstance(engine_report, EvaluationReport)
