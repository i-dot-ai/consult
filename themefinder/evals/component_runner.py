"""Run a component through the configured dataset, runner and artefact ports"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from datasets import DatasetConfig
from eval_types import ComponentConfig

if TYPE_CHECKING:
    from config import EvalBackends


async def run_component(
    component_config: ComponentConfig,
    dataset_config: DatasetConfig,
    backends: EvalBackends,
    *,
    llm: Any,
) -> dict[str, Any]:
    """Load, evaluate and persist cases, returning benchmark-compatible results.

    Case-level failures are recorded with their outcomes. Fatal adapter errors
    propagate to the caller without finalising an incomplete run as successful.
    """

    if component_config.component != dataset_config.component:
        raise ValueError(
            f"Component config {component_config} does not match dataset config {dataset_config.component}"
        )

    cases = backends.dataset.load_cases(dataset_config)
    report = await backends.runner.run(component_config, cases, llm=llm)

    backends.artefacts.start_run(component_config.component, dataset_config.dataset)
    for outcome in report.outcomes:
        backends.artefacts.record_case(outcome)

    return backends.artefacts.finish_run(report, engine_report=report.engine_report)
