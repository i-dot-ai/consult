"""Public API and CLI for running any registered evaluation component."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from themefinder.llm import OpenAILLM

from component_runner import run_component
from components import COMPONENT_NAMES, build_component_config
from config import resolve_backends
from datasets import DatasetConfig
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
        request_kwargs={"temperature": 1},
        base_url=base_url,
        api_key=api_key,
    )


async def evaluate_component(
    component: str,
    dataset: str = "gambling_XS",
    *,
    llm: Any | None = None,
    judge_llm: Any | None = None,
    context: dict[str, Any] | None = None,
    question_num: int | None = None,
    settings: EvalSettings | None = None,
    runs: int = 1,
) -> dict[str, Any]:
    """Build and run one component through the configured framework backends.

    ``runs`` repeats every case so each metric gets a mean and stddev across runs.
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
        # Never fall back to the task model: judge should be independant and consistent
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
        context=context,
        repeat=runs,
    )
    return await run_component(
        component_config,
        dataset_config,
        backends,
        llm=task_llm,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a ThemeFinder evaluation")
    parser.add_argument(
        "--component",
        required=True,
        choices=COMPONENT_NAMES,
        help="Evaluation component to run",
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
        help="Question number to evaluate (mapping only)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Times to run every case, for mean/stddev per metric (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print each case's task output and theme tracks (always saved in results.json)",
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
    args = build_parser().parse_args(argv)

    results = asyncio.run(
        evaluate_component(
            component=args.component,
            dataset=args.dataset,
            question_num=args.question,
            runs=args.runs,
        )
    )

    printed = results if args.verbose else _scores_only(results)
    print(json.dumps(printed, indent=2, sort_keys=True, default=str))

    # Case errors are recorded, not raised, so fail here or DVC and CI would call the run a success.
    results_path = LOCAL_EVAL_RUNS_DIR / args.component / args.dataset / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    errors = count_errors(payload)
    if errors > 0:
        raise SystemExit(f"{errors} case or evaluator errors")


if __name__ == "__main__":
    main()
