"""Langfuse artefact store implementation."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from httpx import RequestError

from eval_types import CaseOutcome, RunReport
from langfuse import propagate_attributes
from utils import stats
from utils import langfuse as langfuse_utils
from utils.langfuse import LangfuseContext
from utils.logging_config import get_logger
from utils.results import count_errors, flatten_run_report, json_safe, serialise_outcome

from .base import ArtefactStorePort


logger = get_logger(__name__)


class LangfuseArtefactStore(ArtefactStorePort):
    def __init__(self, context: LangfuseContext):
        self.context = context
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
                    # Lets score views filter by model and dataset without joining traces
                    "metadata": self.context.metadata,
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
        del engine_report

        results = flatten_run_report(report)
        self._record_run_scores(report, results.get("aggregate"))

        return results

    def _record_run_scores(
        self, report: RunReport, aggregate: dict[str, Any] | None
    ) -> None:
        """Write run-level values as scores on one trace per run, so dashboards can
        compare runs.

        Not also on the dataset run: those copies have no trace, so they show
        unnamed in score views and double-count in averages.
        """
        client = self.context.client
        if client is None:
            return

        scores: dict[str, float | None] = {}
        for metric, summary in stats.summarise_runs(report.outcomes).items():
            scores[f"{metric}_mean"] = summary["mean"]
            scores[f"{metric}_stdev"] = summary["stdev"]
        if aggregate is not None:
            consistency = aggregate[stats.CONSISTENCY_METRIC]
            for metric in stats.CONSISTENCY_SCORES:
                scores[f"{stats.CONSISTENCY_METRIC}_{metric}"] = consistency[metric]
        if report.metrics is not None:
            scores.update(json_safe(report.metrics))
        scores["error_count"] = count_errors(
            {"outcomes": [serialise_outcome(o) for o in report.outcomes]}
        )

        # A plain filter for dashboards to pick out run-level values; str because
        # v4 propagated metadata only takes str
        # n_runs is filterable, so dashboards can exclude values backed by too few runs
        metadata = {
            **(self.context.metadata or {}),
            "aggregate": "true",
            "n_runs": str(report.n_runs),
        }
        with self._new_trace(
            self.aggregate_name,
            metadata=metadata,
            output=json_safe({"scores": scores, "aggregate": aggregate}),
        ) as trace:
            for name, value in scores.items():
                # None means not computable (e.g. stdev of one run), not zero
                if value is None:
                    continue
                client.create_score(
                    trace_id=trace.trace_id,
                    # Attached to the model-named observation, which score views break down by
                    observation_id=trace.id,
                    name=name,
                    value=value,
                    data_type="NUMERIC",
                    metadata=metadata,
                )

    @contextmanager
    def _new_trace(
        self, name: str, *, metadata: dict | None, **observation_kwargs: Any
    ) -> Generator[Any, None, None]:
        """Start a fresh trace whose root observation and trace share one name.

        v4 takes trace input/output from the root observation, and trace-level
        attributes only via propagate_attributes, so every trace needs both.
        """
        client = self.context.client
        with (
            client.start_as_current_observation(
                trace_context={"trace_id": client.create_trace_id()},
                name=name,
                metadata=metadata,
                **observation_kwargs,
            ) as observation,
            propagate_attributes(
                trace_name=name,
                session_id=self.context.session_id,
                tags=self.context.tags,
                metadata=metadata,
            ),
        ):
            yield observation

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

        try:
            with self._new_trace(
                self.case_trace_name(outcome),
                metadata=self.context.metadata,
                input=json_safe(outcome.case.inputs),
                output=json_safe(outcome.output),
                level="ERROR" if outcome.error is not None else "DEFAULT",
                status_message=outcome.error,
            ) as trace:
                if dataset_item_id:
                    self._link_dataset_item_to_trace(
                        client=client,
                        dataset_item_id=str(dataset_item_id),
                        trace_id=trace.trace_id,
                        case_id=outcome.case.id,
                    )
                yield trace, trace.trace_id
        except Exception as exc:
            # Also catches the caller's block (e.g. scoring), so the message stays neutral;
            # the traceback alone doesn't say which case and run the failure belongs to
            logger.error(
                "Langfuse recording failed for case %s and run %s: %s",
                outcome.case.id,
                self._run_name,
                exc,
            )
            raise

    def _link_dataset_item_to_trace(
        self,
        *,
        client: Any,
        dataset_item_id: str,
        trace_id: str,
        case_id: str,
    ) -> None:
        from langfuse.api.core import ApiError

        try:
            langfuse_utils.link_dataset_item(
                client,
                run_name=self._run_name,
                dataset_item_id=dataset_item_id,
                trace_id=trace_id,
                metadata=self.context.metadata,
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

    @property
    def trace_name_prefix(self) -> str:
        """Shared start of every trace name, so a run's traces sort and filter together.

        Score views in v4 events_only mode can only break down by the observation a
        score is attached to, so names carry the model and dataset but not the
        session: runs stay distinguishable by session and timestamp.
        """
        model = (self.context.metadata or {}).get("model", "unknown")
        dataset = self._dataset or "unknown-dataset"
        return f"{self._component}:{model}:{dataset}"

    @property
    def aggregate_name(self) -> str:
        """One name for the run-level trace and its observation, so every view agrees."""
        return f"{self.trace_name_prefix}:aggregate"

    def case_trace_name(self, outcome: CaseOutcome) -> str:
        """Always names the run, 1-based, so single and repeated runs share one shape."""
        return (
            f"{self.trace_name_prefix}:{outcome.case.key}:run_{outcome.run_index + 1}"
        )
