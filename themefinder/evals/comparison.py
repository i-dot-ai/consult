"""Compare chat models from the LLM gateway on the evaluation components.

Every selected model runs the same components the same number of times. Scores
and gateway metrics are aggregated per model and persisted under
``benchmark_results/<id>/``, the layout ``visualise_benchmark.py`` reads.

The single run itself is the ``evaluate`` callable the CLI hands in, so this
module owns selection, retries, aggregation and persistence and never names
the platform a run is traced on.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table

from themefinder.llm import OpenAILLM

from components import COMPONENT_NAMES
from eval_types import RunLabels
from utils import gateway

QUICK_MODEL = "gpt-4.1-sweden-2025-03"
TRANSIENT_ERROR_MARKERS = ("ENOTFOUND", "ECONNREFUSED", "ECONNRESET", "DNS", "503")
RESULTS_DIR_NAME = "benchmark_results"

console = Console()

Evaluate = Callable[..., Awaitable[dict[str, Any]]]


def _is_transient(error: Exception) -> bool:
    """A network blip worth retrying, as opposed to a failure the next attempt would repeat."""
    error_text = str(error)
    return (
        any(marker in error_text for marker in TRANSIENT_ERROR_MARKERS)
        or "temporarily unavailable" in error_text.lower()
    )


class ValidationErrorCounter(logging.Handler):
    """Logging handler that counts validation warnings/errors from themefinder."""

    # Only count warnings from these logger namespaces
    TRACKED_LOGGERS = ("themefinder",)

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        """Reset counters for a new eval run."""
        self.validation_errors = 0
        self.total_warnings = 0
        self.error_details: list[str] = []

    def emit(self, record: logging.LogRecord):
        """Count validation-related log messages from tracked loggers."""
        if not record.name.startswith(self.TRACKED_LOGGERS):
            return

        if record.levelno >= logging.WARNING:
            self.total_warnings += 1
            message = record.getMessage()
            if "validation error" in message.lower():
                self.validation_errors += 1
                self.error_details.append(message[:200])


# Run context for structured logging: (model, component, run_number)
_run_context: ContextVar[tuple[str, str, int] | None] = ContextVar(
    "_run_context", default=None
)


class _SingleLineFormatter(logging.Formatter):
    """Collapses multiline messages onto a single line for grepability."""

    def format(self, record: logging.LogRecord) -> str:
        result = super().format(record)
        return result.replace("\n", "\\n")


class RunLogFilter(logging.Filter):
    """Injects the run context into log records and filters by namespace."""

    ACCEPTED_PREFIXES = ("themefinder", "theme_finder", "synthetic")

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name
        is_relevant = (
            name.startswith(self.ACCEPTED_PREFIXES)
            or "/themefinder/" in name  # models.py uses __file__ as logger name
        )
        if not is_relevant:
            return False

        context = _run_context.get(None)
        if context is not None:
            record.model_name, record.component, record.run_number = context
        else:
            record.model_name = "-"
            record.component = "-"
            record.run_number = "-"

        return True


@dataclass
class ModelConfig:
    """Configuration for a single model variant, resolved from the gateway.

    `name` is the gateway's model_group name, used both for display and as
    the `model=` value sent to the gateway.
    """

    name: str
    reasoning_effort: str | None = None  # low/medium/high, for reasoning-capable models
    temperature: float = 0.0
    timeout: int = 600  # 10 min default

    def create_llm(self) -> OpenAILLM:
        """Create an OpenAILLM instance via the LLM gateway."""
        request_kwargs: dict[str, Any] = {}
        if not self.reasoning_effort:
            request_kwargs["temperature"] = self.temperature
        base_url, api_key = gateway.gateway_credentials()
        return OpenAILLM(
            model=self.name,
            request_kwargs=request_kwargs,
            base_url=base_url,
            api_key=api_key,
            timeout=self.timeout,
        )

    @property
    def tag(self) -> str:
        """Name that tells variants of one model apart in results and traces."""
        if self.reasoning_effort:
            return f"{self.name}_{self.reasoning_effort}"
        return self.name


def to_model_configs(
    gateway_model: gateway.GatewayModel, reasoning_efforts: list[str]
) -> list[ModelConfig]:
    """Expand one gateway model into one ModelConfig per requested effort level.

    Only reasoning-capable models are affected; everything else always gets
    exactly one config, regardless of --reasoning-effort.
    """
    if not gateway_model.supports_reasoning:
        return [ModelConfig(name=gateway_model.name)]
    return [
        ModelConfig(name=gateway_model.name, reasoning_effort=effort)
        for effort in reasoning_efforts
    ]


@dataclass
class ComparisonConfig:
    """What to compare: the models, the components and how often."""

    dataset: str
    models: list[ModelConfig]
    runs_per_model: int = 5
    components: list[str] = field(default_factory=lambda: list(COMPONENT_NAMES))
    judge_model: str | None = None  # Gateway model name for the judge LLM


@dataclass
class RunResult:
    """Result from a single evaluation run."""

    model: str
    model_tag: str
    run_number: int
    component: str
    dataset: str
    session_id: str
    scores: dict[str, float]
    timestamp: datetime
    outputs: dict[str, Any] = field(default_factory=dict)  # Non-numeric outputs

    # Metrics aggregated from each gateway response in this evaluation run.
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_seconds: float | None = None
    # Deprecated end-to-end duration retained for existing CSV consumers.
    duration_seconds: float | None = None
    processing_time_seconds: float | None = None
    llm_call_count: int = 0


def _metric_float(metrics: dict[str, Any] | None, key: str) -> float | None:
    """Read one optional floating-point metric from an evaluation result."""
    if metrics is None or metrics.get(key) is None:
        return None
    value = metrics[key]
    if isinstance(value, bool):
        raise TypeError(f"Evaluation metric {key!r} must be a number or null")
    return float(value)


def _metric_int(metrics: dict[str, Any] | None, key: str) -> int | None:
    """Read one optional integer metric from an evaluation result."""
    if metrics is None or metrics.get(key) is None:
        return None
    value = metrics[key]
    if isinstance(value, bool) or int(value) != value:
        raise TypeError(f"Evaluation metric {key!r} must be an integer or null")
    return int(value)


class ComparisonRunner:
    """Runs every component for every model and collects the results."""

    def __init__(
        self,
        config: ComparisonConfig,
        evaluate: Evaluate,
        output_dir: str = RESULTS_DIR_NAME,
    ):
        self.config = config
        self.evaluate = evaluate
        self.results: list[RunResult] = []
        self.comparison_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir
        self._output_path: Path | None = None
        self._results_lock = asyncio.Lock()

    def _create_log_handler(self) -> logging.FileHandler:
        """Create file handler for structured run logging."""
        log_path = self.get_output_path() / "benchmark.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            _SingleLineFormatter(
                "%(asctime)s | %(component)s | %(model_name)s | run:%(run_number)s"
                " | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler.addFilter(RunLogFilter())
        return handler

    async def run(self) -> list[RunResult]:
        """Execute the full comparison with models in parallel, variants sequential."""
        root_logger = logging.getLogger()
        original_level = root_logger.level
        log_handler = self._create_log_handler()
        root_logger.addHandler(log_handler)
        root_logger.setLevel(logging.DEBUG)

        try:
            return await self._run_comparison()
        finally:
            root_logger.removeHandler(log_handler)
            log_handler.close()
            root_logger.setLevel(original_level)

    async def _run_comparison(self) -> list[RunResult]:
        """Inner execution (wrapped by run() for logging setup)."""
        total_runs = (
            len(self.config.models)
            * self.config.runs_per_model
            * len(self.config.components)
        )
        runs_per_model = self.config.runs_per_model * len(self.config.components)

        # Group by name to avoid rate-limit contention: --reasoning-effort can
        # produce multiple ModelConfigs sharing one gateway model (e.g. the
        # same model at low/medium/high), and those share one underlying
        # deployment, so they're run sequentially within a group rather than
        # firing concurrent requests at the same rate-limited resource.
        # Distinct models (different groups) still run fully in parallel.
        name_groups: dict[str, list[ModelConfig]] = {}
        for model in self.config.models:
            name_groups.setdefault(model.name, []).append(model)

        console.print(
            f"\n[bold cyan]Starting comparison: {self.comparison_id}[/bold cyan]"
        )
        console.print(f"  Dataset: {self.config.dataset}")
        console.print(
            f"  Models: {len(self.config.models)} across {len(name_groups)} distinct"
        )
        console.print(f"  Runs per model: {self.config.runs_per_model}")
        console.print(f"  Components: {', '.join(self.config.components)}")
        console.print(f"  Total runs: {total_runs} ({runs_per_model} per model)\n")

        group_tasks = [self._run_model_group(models) for models in name_groups.values()]
        results = await asyncio.gather(*group_tasks, return_exceptions=True)

        for name, result in zip(name_groups.keys(), results):
            if isinstance(result, Exception):
                console.print(f"[bold red][{name}] FAILED: {result}[/bold red]")

        return self.results

    async def _run_model_group(self, models: list[ModelConfig]) -> list[RunResult]:
        """Run all variants (e.g. reasoning-effort levels) of one model sequentially.

        Sequential on purpose: variants share one underlying gateway
        deployment, so running them concurrently would contend for that
        deployment's rate limit instead of just this group's own pacing.
        """
        group_results = []
        for model_config in models:
            model_results = await self._run_model(model_config)
            group_results.extend(model_results)
        return group_results

    async def _run_model(self, model_config: ModelConfig) -> list[RunResult]:
        """Run all components for a single model (sequential within model)."""
        error_counter = ValidationErrorCounter()
        logging.getLogger().addHandler(error_counter)
        judge_llm = self._create_judge_llm()

        model_results = []
        runs_per_model = self.config.runs_per_model * len(self.config.components)
        current = 0

        try:
            for run_number in range(1, self.config.runs_per_model + 1):
                for component in self.config.components:
                    current += 1
                    console.print(
                        f"[bold][{model_config.tag}][/bold] "
                        f"[{current}/{runs_per_model}] Run {run_number} | {component}"
                    )

                    max_eval_retries = 3
                    retry_delay = 2.0

                    for attempt in range(max_eval_retries):
                        try:
                            result = await self._run_single_eval(
                                model_config=model_config,
                                run_number=run_number,
                                component=component,
                                error_counter=error_counter,
                                judge_llm=judge_llm,
                            )
                            model_results.append(result)

                            async with self._results_lock:
                                self.results.append(result)
                                self._print_scores(result.scores)
                                self._save_incremental()
                                self._save_outputs(result)
                            break

                        except Exception as error:
                            if _is_transient(error) and attempt < max_eval_retries - 1:
                                delay = retry_delay * (2**attempt)
                                console.print(
                                    f"  [yellow]Transient error (attempt {attempt + 1}/{max_eval_retries}), "
                                    f"retrying in {delay:.1f}s...[/yellow]"
                                )
                                await asyncio.sleep(delay)
                                continue

                            console.print(
                                f"  [bold][{model_config.tag}][/bold] [red]ERROR: {error}[/red]"
                            )
                            break

        finally:
            logging.getLogger().removeHandler(error_counter)

        console.print(f"[bold green][{model_config.tag}] Complete![/bold green]")
        return model_results

    def _create_judge_llm(self) -> OpenAILLM | None:
        """One judge per model run.

        A model's runs reuse it, but models run concurrently and the tracer rebinds
        the judge's client to each run, so it is never shared across models.
        """
        if not self.config.judge_model:
            return None
        base_url, api_key = gateway.gateway_credentials()
        return OpenAILLM(
            model=self.config.judge_model,
            request_kwargs={"temperature": 0},
            base_url=base_url,
            api_key=api_key,
            timeout=600,
        )

    async def _run_single_eval(
        self,
        model_config: ModelConfig,
        run_number: int,
        component: str,
        error_counter: ValidationErrorCounter,
        judge_llm: OpenAILLM | None,
    ) -> RunResult:
        """Run a single evaluation under its logging context."""
        token = _run_context.set((model_config.name, component, run_number))
        try:
            return await asyncio.wait_for(
                self._execute_eval(
                    model_config, run_number, component, error_counter, judge_llm
                ),
                timeout=1200,
            )
        finally:
            _run_context.reset(token)

    async def _execute_eval(
        self,
        model_config: ModelConfig,
        run_number: int,
        component: str,
        error_counter: ValidationErrorCounter,
        judge_llm: OpenAILLM | None,
    ) -> RunResult:
        """Execute a single evaluation (called within the run context)."""
        error_counter.reset()

        session_id = (
            f"benchmark_{self.comparison_id}_"
            f"{model_config.tag}_{component}_run{run_number}"
        )
        labels = RunLabels(
            name=session_id,
            tags=(
                f"model:{model_config.tag}",
                f"run:{run_number}",
                f"benchmark:{self.comparison_id}",
            ),
            metadata={
                "benchmark_id": self.comparison_id,
                "model": model_config.name,
                "model_tag": model_config.tag,
                "reasoning_effort": model_config.reasoning_effort,
                "run_number": run_number,
            },
        )

        llm = model_config.create_llm()

        # duration_seconds keeps its former scope, the whole evaluate call
        # including artefact finalisation; processing_time_seconds is the
        # component runner's own narrower measurement.
        started_at = time.perf_counter()
        scores = await self.evaluate(
            component=component,
            dataset=self.config.dataset,
            llm=llm,
            # Mapping has no judge evaluator, and passing one only earns a warning per run.
            judge_llm=None if component == "mapping" else judge_llm,
            labels=labels,
        )
        duration_seconds = time.perf_counter() - started_at

        all_scores = {}
        all_outputs = {}
        metrics = (scores or {}).get("metrics")
        if metrics is not None and not isinstance(metrics, dict):
            raise TypeError("Evaluation metrics must be returned as a dictionary")
        for key, value in (scores or {}).items():
            if key == "metrics":
                continue
            if isinstance(value, (int, float)):
                all_scores[key] = value
            else:
                all_outputs[key] = value

        all_scores["validation_errors"] = error_counter.validation_errors
        all_scores["total_warnings"] = error_counter.total_warnings

        processing_time_seconds = _metric_float(metrics, "processing_time_seconds")
        return RunResult(
            model=model_config.name,
            model_tag=model_config.tag,
            run_number=run_number,
            component=component,
            dataset=self.config.dataset,
            session_id=session_id,
            scores=all_scores,
            outputs=all_outputs,
            timestamp=datetime.now(),
            input_tokens=_metric_int(metrics, "input_tokens"),
            output_tokens=_metric_int(metrics, "output_tokens"),
            total_tokens=_metric_int(metrics, "total_tokens"),
            cost_usd=_metric_float(metrics, "cost_usd"),
            latency_seconds=_metric_float(metrics, "latency_seconds"),
            duration_seconds=duration_seconds,
            processing_time_seconds=processing_time_seconds,
            llm_call_count=_metric_int(metrics, "llm_call_count") or 0,
        )

    def _print_scores(self, scores: dict[str, float]) -> None:
        """Print scores inline."""
        if not scores:
            console.print("  [dim]No scores returned[/dim]")
            return

        validation_errors = scores.get("validation_errors", 0)
        other_scores = {
            name: value
            for name, value in scores.items()
            if name not in ("validation_errors", "total_warnings")
            and isinstance(value, (int, float))
        }

        score_texts = [f"{name}: {value:.3f}" for name, value in other_scores.items()]

        if score_texts:
            console.print(f"  [green]{', '.join(score_texts)}[/green]", end="")

        if validation_errors > 0:
            console.print(
                f"  [yellow]({validation_errors} validation retries)[/yellow]"
            )
        else:
            console.print()

    def get_output_path(self) -> Path:
        """Get or create the output directory for this comparison."""
        if self._output_path is None:
            self._output_path = Path(self.output_dir) / self.comparison_id
            self._output_path.mkdir(parents=True, exist_ok=True)
        return self._output_path

    def _save_incremental(self) -> None:
        """Save current results incrementally."""
        output_path = self.get_output_path()

        raw_df = self.generate_summary_table()
        raw_df.to_csv(output_path / "raw_results.csv", index=False)

        # The keys are the contract visualise_benchmark.py reads.
        config_dict = {
            "benchmark_id": self.comparison_id,
            "dataset": self.config.dataset,
            "runs_per_model": self.config.runs_per_model,
            "evals": self.config.components,
            "judge_model": self.config.judge_model,
            "models": [
                {"name": model.name, "reasoning_effort": model.reasoning_effort}
                for model in self.config.models
            ],
        }
        with open(output_path / "config.json", "w") as config_file:
            json.dump(config_dict, config_file, indent=2)

    def _save_outputs(self, result: RunResult) -> None:
        """Save non-numeric pipeline outputs as JSON for a single run."""
        if not result.outputs:
            return

        outputs_dir = self.get_output_path() / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        filename = f"{result.model_tag}_{result.component}_run{result.run_number}.json"
        with open(outputs_dir / filename, "w") as outputs_file:
            json.dump(result.outputs, outputs_file, indent=2, default=str)

    def generate_summary_table(self) -> pd.DataFrame:
        """Generate summary DataFrame from results."""
        if not self.results:
            return pd.DataFrame()

        rows = []
        for result in self.results:
            row = {
                "model": result.model,
                "model_tag": result.model_tag,
                "run": result.run_number,
                "eval": result.component,
                "session_id": result.session_id,
                # Kept for consumers of the former benchmark CSV schema.
                "duration_seconds": result.duration_seconds,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "cost_usd": result.cost_usd,
                "latency_seconds": result.latency_seconds,
                "processing_time_seconds": result.processing_time_seconds,
                "llm_call_count": result.llm_call_count,
            }
            for score_name, score_value in result.scores.items():
                if isinstance(score_value, (int, float)):
                    row[score_name] = score_value
            rows.append(row)

        return pd.DataFrame(rows)

    def generate_aggregated_table(self) -> pd.DataFrame:
        """Generate aggregated results (mean ± std) per model/component."""
        summary = self.generate_summary_table()
        if summary.empty:
            return summary

        metadata_columns = {"model", "model_tag", "run", "eval", "session_id"}
        score_columns = [
            column for column in summary.columns if column not in metadata_columns
        ]

        if not score_columns:
            return pd.DataFrame()

        aggregated_rows = []
        for (model_tag, component), group in summary.groupby(["model_tag", "eval"]):
            row = {"model_tag": model_tag, "eval": component, "n_runs": len(group)}
            for column in score_columns:
                if column in group.columns:
                    values = group[column].dropna()
                    if len(values) > 0:
                        row[f"{column}_mean"] = values.mean()
                        row[f"{column}_std"] = values.std()
            aggregated_rows.append(row)

        return pd.DataFrame(aggregated_rows)

    def print_results_table(self) -> None:
        """Print results as Rich tables, one per component."""
        aggregated = self.generate_aggregated_table()
        if aggregated.empty:
            console.print("[yellow]No results to display[/yellow]")
            return

        console.print("\n[bold cyan]Comparison Results Summary[/bold cyan]\n")

        for component in self.config.components:
            component_rows = aggregated[aggregated["eval"] == component]
            if component_rows.empty:
                continue

            table = Table(title=f"{component.title()} Evaluation")
            table.add_column("Model", style="cyan")
            table.add_column("Runs", justify="right")

            mean_columns = [
                column for column in component_rows.columns if column.endswith("_mean")
            ]
            for column in mean_columns:
                table.add_column(column.replace("_mean", ""), justify="right")

            for _, row in component_rows.iterrows():
                values = [str(row["model_tag"]), str(int(row["n_runs"]))]
                for column in mean_columns:
                    mean = row.get(column, float("nan"))
                    std = row.get(column.replace("_mean", "_std"), float("nan"))
                    if pd.notna(mean):
                        values.append(f"{mean:.3f} ± {std:.3f}")
                    else:
                        values.append("-")
                table.add_row(*values)

            console.print(table)
            console.print()

    def save_results(self) -> None:
        """Save final aggregated results."""
        output_path = self.get_output_path()

        raw_df = self.generate_summary_table()
        raw_df.to_csv(output_path / "raw_results.csv", index=False)

        aggregated = self.generate_aggregated_table()
        aggregated.to_csv(output_path / "aggregated_results.csv", index=False)

        console.print(f"[green]Results saved to {output_path}[/green]")


def print_cost_summary(results_df: pd.DataFrame) -> None:
    """Print gateway-supplied cost and timing totals by model."""
    if results_df.empty:
        return

    console.print("\n[bold cyan]Gateway Metrics Summary[/bold cyan]\n")

    metric_columns = [
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost_usd",
        "latency_seconds",
        "processing_time_seconds",
    ]
    totals = (
        results_df.groupby("model_tag")[metric_columns]
        .agg(lambda values: values.sum(min_count=1))
        .reset_index()
    )

    def format_count(value: float) -> str:
        return "-" if pd.isna(value) else f"{int(value):,}"

    def format_decimal(value: float, prefix: str = "") -> str:
        return "-" if pd.isna(value) else f"{prefix}{value:.4f}"

    def format_seconds(value: float) -> str:
        return "-" if pd.isna(value) else f"{value:.1f}s"

    table = Table(title="Total Costs by Model")
    table.add_column("Model", style="cyan")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Cost (USD)", justify="right", style="green")
    table.add_column("Summed Gateway Latency", justify="right")
    table.add_column("Processing Time", justify="right")

    for _, row in totals.iterrows():
        table.add_row(
            row["model_tag"],
            format_count(row["input_tokens"]),
            format_count(row["output_tokens"]),
            format_count(row["total_tokens"]),
            format_decimal(row["cost_usd"], "$"),
            format_seconds(row["latency_seconds"]),
            format_seconds(row["processing_time_seconds"]),
        )

    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{format_count(totals['input_tokens'].sum(min_count=1))}[/bold]",
        f"[bold]{format_count(totals['output_tokens'].sum(min_count=1))}[/bold]",
        f"[bold]{format_count(totals['total_tokens'].sum(min_count=1))}[/bold]",
        f"[bold green]{format_decimal(totals['cost_usd'].sum(min_count=1), '$')}[/bold green]",
        f"[bold]{format_seconds(totals['latency_seconds'].sum(min_count=1))}[/bold]",
        f"[bold]{format_seconds(totals['processing_time_seconds'].sum(min_count=1))}[/bold]",
    )

    console.print(table)


def is_comparison(args: argparse.Namespace) -> bool:
    """A model selector or the quick preset makes the run a comparison."""
    return bool(args.models or args.family or args.all or args.quick)


def apply_quick_preset(args: argparse.Namespace) -> None:
    """Apply --quick's fully self-contained preset, overriding any other selector."""
    if not args.quick:
        return
    args.dataset = "gambling_XS"
    args.runs = 1
    # A smoke test pins one model so it stays fast and comparable between CI runs.
    args.models = [QUICK_MODEL]
    args.family = None
    args.all = False


def validate_selector_args(args: argparse.Namespace) -> str | None:
    """Return an error message if not exactly one of --models/--family/--all was given."""
    if sum((bool(args.models), bool(args.family), args.all)) != 1:
        return "Exactly one of --models, --family, or --all is required."
    return None


def select_named_models(
    gateway_models: list[gateway.GatewayModel], names: list[str]
) -> tuple[list[gateway.GatewayModel], list[str], list[gateway.GatewayModel]]:
    """--models: exact-name lookup. Unhealthy matches are still selected (the
    user asked for them by name), just flagged for a warning, not dropped.

    Returns (selected, missing, unhealthy).
    """
    found, missing = gateway.select_by_name(gateway_models, names)
    _, unhealthy = gateway.split_unhealthy(found)
    return found, missing, unhealthy


def select_healthy_models(
    gateway_models: list[gateway.GatewayModel], families: list[str] | None
) -> tuple[list[gateway.GatewayModel], list[gateway.GatewayModel]]:
    """--family/--all: broad selection, unhealthy models dropped (not just warned).

    Returns (selected, excluded).
    """
    candidates = (
        gateway.filter_by_family(gateway_models, families)
        if families
        else gateway_models
    )
    return gateway.split_unhealthy(candidates)


async def select_models(args: argparse.Namespace) -> list[ModelConfig]:
    """Resolve the CLI selector against the gateway, failing fast on a bad name."""
    # Dedupe --models so a copy-paste typo can't produce two variants of the
    # same model running concurrently against each other.
    if args.models:
        args.models = list(dict.fromkeys(args.models))

    gateway_models = await gateway.discover_chat_models()

    if args.models:
        selected, missing, unhealthy = select_named_models(gateway_models, args.models)
        if missing:
            # Fail fast rather than silently running a smaller comparison than
            # requested: a name that doesn't match is almost always a typo or
            # a stale model reference, not something to route around.
            available = sorted(model.name for model in gateway_models)
            console.print(
                f"[red]No matching models: {missing}. Available: {available}[/red]"
            )
            sys.exit(1)
        for model in unhealthy:
            console.print(
                f"[yellow]Warning: {model.name} is reported unhealthy by the gateway, "
                "proceeding anyway[/yellow]"
            )
    else:
        selected, excluded = select_healthy_models(gateway_models, args.family)
        if excluded:
            console.print(
                f"[dim]Excluded {len(excluded)} unhealthy model(s), not run: "
                f"{[model.name for model in excluded]}[/dim]"
            )

    if not selected:
        console.print("[red]No models matched the given selector.[/red]")
        sys.exit(1)

    return [
        model_config
        for gateway_model in selected
        for model_config in to_model_configs(gateway_model, args.reasoning_effort)
    ]


async def run_comparison(args: argparse.Namespace, evaluate: Evaluate) -> None:
    """Run the comparison the CLI asked for, then report and persist it."""
    # gRPC 1.58+ ships a C-ares resolver that fails on some networks; the native one must be
    # chosen before anything imports gRPC during the run.
    os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
    models = await select_models(args)
    config = ComparisonConfig(
        dataset=args.dataset,
        models=models,
        runs_per_model=args.runs,
        components=args.component or list(COMPONENT_NAMES),
        judge_model=args.judge_model,
    )
    runner = ComparisonRunner(config, evaluate)

    console.print("\n[bold cyan]ThemeFinder model comparison[/bold cyan]")
    console.print(f"  Models: {[model.name for model in models]}")
    console.print()

    try:
        await runner.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Comparison interrupted[/yellow]")

    runner.print_results_table()

    if not runner.results:
        console.print(
            "[bold red]No results collected: all evals failed "
            "(check for authentication errors above)[/bold red]"
        )
        sys.exit(1)

    # Metrics come straight from the gateway responses, with no post-hoc reconciliation.
    print_cost_summary(runner.generate_summary_table())

    runner.save_results()

    try:
        # The report is a bonus, so a broken report module must not fail the comparison.
        from visualise_benchmark import generate_html_report, load_benchmark_data

        data = load_benchmark_data(runner.comparison_id)
        report_path = str(runner.get_output_path() / "report.html")
        generate_html_report(data, report_path)
        console.print(f"[green]HTML report: {report_path}[/green]")
    except Exception as error:
        console.print(f"[yellow]Could not generate HTML report: {error}[/yellow]")

    # Machine-parseable output for CI
    print(f"BENCHMARK_ID={runner.comparison_id}")
