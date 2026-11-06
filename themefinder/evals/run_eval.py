"""Public API and CLI for evaluating components, alone or across models.

One command serves both: ``--component <name>`` runs a single model through
one component, and any model selector (``--models``, ``--family``, ``--all``
or ``--quick``) turns the run into a model comparison.
"""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from themefinder.llm import OpenAILLM

import comparison
from component_runner import run_component
from components import COMPONENT_NAMES, build_component_config
from config import resolve_backends
from datasets import DatasetConfig
from eval_types import RunLabels
from settings import EvalSettings, eval_settings
from utils import gateway, stats
from utils.logging_config import get_logger
from utils.results import count_errors

logger = get_logger(__name__)

LOCAL_EVAL_RUNS_DIR = Path(__file__).resolve().parent / "local_eval_runs"


def _create_llm(settings: EvalSettings, model: str | None) -> OpenAILLM:
    """Build a gateway model from one consistent settings snapshot."""
    base_url, api_key = gateway.gateway_credentials(settings=settings)
    return OpenAILLM(
        model=model,
        request_kwargs={"temperature": 0},
        base_url=base_url,
        api_key=api_key,
    )


async def evaluate_component(
    component: str,
    dataset: str = "gambling_XS",
    *,
    llm: Any | None = None,
    judge_llm: Any | None = None,
    labels: RunLabels | None = None,
    question_num: int | None = None,
    settings: EvalSettings | None = None,
    runs: int = 1,
) -> dict[str, Any]:
    """Build and run one component through the configured framework backends.

    ``labels`` name and tag the run wherever it is recorded. ``runs`` repeats
    every case so each metric gets a mean and stddev across runs.
    """
    if component not in COMPONENT_NAMES:
        raise ValueError(
            f"Unknown component '{component}'. Must be one of: {list(COMPONENT_NAMES)}"
        )

    settings = settings if settings is not None else eval_settings
    if component == "mapping":
        if judge_llm is not None:
            logger.warning(
                "judge_llm is ignored for mapping because it has no judge evaluator"
            )
    elif judge_llm is None:
        # Never fall back to the task model: judge should be independent and consistent
        if not settings.judge_model:
            raise ValueError(f"AUTO_EVAL_JUDGE_MODEL must be set for {component}")
        judge_llm = _create_llm(settings, settings.judge_model)
    task_llm = (
        llm if llm is not None else _create_llm(settings, settings.auto_eval_model)
    )
    dataset_config = DatasetConfig(dataset=dataset, component=component)
    component_config = build_component_config(
        component,
        judge_llm=judge_llm,
        question_num=question_num,
    )
    backends = resolve_backends(
        dataset_config,
        settings=settings,
        labels=labels,
        repeat=runs,
    )
    backends.tracer.observe(task_llm)
    if judge_llm is not None:
        backends.tracer.observe(judge_llm)
    return await run_component(
        component_config,
        dataset_config,
        backends,
        llm=task_llm,
    )


EXAMPLES = """
Examples:
  # One component, one model (AUTO_EVAL_MODEL)
  uv run python run_eval.py --component generation --dataset gambling_XS

  # Every healthy chat model on the gateway, all components
  uv run python run_eval.py --all --dataset housing_S --runs 3

  # One or more vendor families
  uv run python run_eval.py --family gemini claude --dataset housing_S

  # Specific models by exact gateway name, mapping only
  uv run python run_eval.py --models gpt-4o-uk gemini-3.5-flash-uk --component mapping
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a ThemeFinder evaluation, or compare models on it",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES,
    )
    parser.add_argument(
        "--component",
        nargs="+",
        choices=COMPONENT_NAMES,
        default=None,
        help="Component(s) to evaluate. A single run takes exactly one; "
        "a comparison defaults to all of them",
    )
    parser.add_argument(
        "--dataset",
        default="gambling_XS",
        help="Dataset identifier (default: gambling_XS)",
    )
    parser.add_argument(
        "--question",
        type=int,
        default=None,
        help="Question number to evaluate (single mapping runs only)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Single run: times to run every case, for mean/stddev per metric. "
        "Comparison: full runs per model (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print each case's task output and theme tracks (always saved in results.json)",
    )

    comparison_group = parser.add_argument_group(
        "model comparison",
        "Any model selector compares models instead of running the default one",
    )
    comparison_group.add_argument(
        "--models",
        nargs="+",
        help="Exact gateway model name(s) to compare",
    )
    comparison_group.add_argument(
        "--family",
        nargs="+",
        choices=gateway.KNOWN_FAMILIES,
        help="Vendor famil(y/ies) to compare, e.g. --family gemini claude",
    )
    comparison_group.add_argument(
        "--all",
        action="store_true",
        help="Compare every healthy chat model discovered on the gateway",
    )
    comparison_group.add_argument(
        "--reasoning-effort",
        nargs="+",
        choices=["low", "medium", "high"],
        default=None,
        help="Reasoning effort level(s) for reasoning-capable models "
        "(default: low). No effect on models that don't support reasoning; "
        "passing multiple levels runs each as a separate model variant.",
    )
    comparison_group.add_argument(
        "--judge-model",
        default=None,
        help="Gateway model name for the judge LLM (default: AUTO_EVAL_JUDGE_MODEL). "
        "Required for every component except mapping; the judge never falls back to "
        "the task model.",
    )
    comparison_group.add_argument(
        "--quick",
        action="store_true",
        help=f"Quick CI smoke test: gambling_XS dataset, 1 run, {comparison.QUICK_MODEL} only.",
    )
    return parser


def _scores_only(results: dict[str, Any]) -> dict[str, Any]:
    """Drop per-case task outputs and theme tracks, which bury the scores on the
    terminal. Works on copies so the caller's results are untouched."""
    printed = {
        key: value for key, value in results.items() if not key.endswith("_output")
    }
    consistency = printed.get("aggregate", {}).get(stats.CONSISTENCY_METRIC)
    if consistency:
        printed["aggregate"] = {
            **printed["aggregate"],
            stats.CONSISTENCY_METRIC: {
                **consistency,
                "by_case": {
                    case: {k: v for k, v in scores.items() if k != "tracks"}
                    for case, scores in consistency["by_case"].items()
                },
            },
        }
    return printed


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if comparison.is_comparison(args):
        comparison.apply_quick_preset(args)
        selector_error = comparison.validate_selector_args(args)
        if selector_error:
            parser.error(selector_error)
        if args.question is not None:
            parser.error("--question applies to a single mapping run, not a comparison")
        if args.verbose:
            parser.error(
                "--verbose applies to a single run; a comparison always saves outputs"
            )
        if args.reasoning_effort is None:
            args.reasoning_effort = ["low"]
        args.judge_model = args.judge_model or eval_settings.judge_model
        judged_components = [
            component
            for component in (args.component or COMPONENT_NAMES)
            if component != "mapping"
        ]
        if judged_components and not args.judge_model:
            parser.error(
                "--judge-model or AUTO_EVAL_JUDGE_MODEL is required for judged components"
            )
        asyncio.run(comparison.run_comparison(args, evaluate_component))
        return

    if args.component is None or len(args.component) != 1:
        parser.error("A single run takes exactly one --component")
    if args.judge_model is not None or args.reasoning_effort is not None:
        parser.error("--judge-model and --reasoning-effort apply to model comparisons")
    component = args.component[0]

    results = asyncio.run(
        evaluate_component(
            component=component,
            dataset=args.dataset,
            question_num=args.question,
            runs=args.runs,
        )
    )

    printed = results if args.verbose else _scores_only(results)
    print(json.dumps(printed, indent=2, sort_keys=True, default=str))

    # Case errors are recorded, not raised, so fail here or DVC and CI would call the run a success.
    results_path = LOCAL_EVAL_RUNS_DIR / component / args.dataset / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    errors = count_errors(payload)
    if errors > 0:
        raise SystemExit(f"{errors} case or evaluator errors")


if __name__ == "__main__":
    main()
