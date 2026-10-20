"""Run a component through the configured dataset, runner and artefact ports"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from datasets import DatasetConfig
from eval_types import ComponentConfig, RunMetrics

from themefinder.llm import collect_gateway_metrics

if TYPE_CHECKING:
    from config import EvalBackends


def _per_run(total: float | None, n_runs: int) -> float | None:
    return None if total is None else total / n_runs


def _per_run_count(total: int | None, n_runs: int) -> int | None:
    """Rounded, since a fractional call or token count reads as nonsense and
    benchmark.py rejects non-integer counts."""
    return None if total is None else round(total / n_runs)


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
    try:
        with collect_gateway_metrics() as gateway_metrics:
            cases = backends.dataset.load_cases(dataset_config)
            report = await backends.runner.run(component_config, cases, llm=llm)
            loaded_at = time.perf_counter()

            backends.artefacts.start_run(
                component_config.component, dataset_config.dataset
            )
            for outcome in report.outcomes:
                backends.artefacts.record_case(outcome)

            gateway_summary = gateway_metrics.summary()

        # Totals cover every repeat, so divide to report what one run costs
        n_runs = backends.runner.repeat
        # Loading happens once however many repeats, so only the repeated part is divided
        load_seconds = loaded_at - started_at
        repeated_seconds = time.perf_counter() - loaded_at
        report.metrics = RunMetrics(
            cost_usd=_per_run(gateway_summary.cost_usd, n_runs),
            latency_seconds=_per_run(gateway_summary.latency_seconds, n_runs),
            processing_time_seconds=load_seconds + repeated_seconds / n_runs,
            llm_call_count=_per_run_count(gateway_summary.call_count, n_runs),
            input_tokens=_per_run_count(gateway_summary.input_tokens, n_runs),
            output_tokens=_per_run_count(gateway_summary.output_tokens, n_runs),
            total_tokens=_per_run_count(gateway_summary.total_tokens, n_runs),
            n_runs=n_runs,
        )
        return backends.artefacts.finish_run(report, engine_report=report.engine_report)
    finally:
        # Flush contexts we created, including when Langfuse is only the dataset.
        backends.close()
