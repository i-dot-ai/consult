"""Run a component through the configured dataset, runner and artefact ports"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from datasets import DatasetConfig
from eval_types import ComponentConfig, RunMetrics

from themefinder.llm import collect_gateway_metrics

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

    started_at = time.perf_counter()
    with collect_gateway_metrics() as gateway_metrics:
        cases = backends.dataset.load_cases(dataset_config)
        report = await backends.runner.run(component_config, cases, llm=llm)

        backends.artefacts.start_run(component_config.component, dataset_config.dataset)
        for outcome in report.outcomes:
            backends.artefacts.record_case(outcome)

        gateway_summary = gateway_metrics.summary()
        report.metrics = RunMetrics(
            cost_usd=gateway_summary.cost_usd,
            latency_seconds=gateway_summary.latency_seconds,
            processing_time_seconds=time.perf_counter() - started_at,
            llm_call_count=gateway_summary.call_count,
            input_tokens=gateway_summary.input_tokens,
            output_tokens=gateway_summary.output_tokens,
            total_tokens=gateway_summary.total_tokens,
        )
        return backends.artefacts.finish_run(report, engine_report=report.engine_report)
