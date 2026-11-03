"""Compose a primary artefact store with one or more secondary stores."""

from typing import Any

from eval_types import CaseOutcome, RunReport

from .base import ArtefactStorePort


class CompositeArtefactStore(ArtefactStorePort):
    """Forward lifecycle events to every store and return the primary result."""

    def __init__(
        self,
        primary: ArtefactStorePort,
        *secondary: ArtefactStorePort,
    ) -> None:
        self.primary = primary
        self.secondary = secondary

    def start_run(self, component: str, dataset: str) -> None:
        self.primary.start_run(component, dataset)
        for store in self.secondary:
            store.start_run(component, dataset)

    def record_case(self, outcome: CaseOutcome) -> None:
        self.primary.record_case(outcome)
        for store in self.secondary:
            store.record_case(outcome)

    def finish_run(
        self,
        report: RunReport,
        *,
        engine_report: Any | None = None,
    ) -> dict[str, Any]:
        results = self.primary.finish_run(report, engine_report=engine_report)
        for store in self.secondary:
            store.finish_run(report, engine_report=engine_report)
        return results
