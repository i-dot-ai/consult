"""Public API and CLI for running any registered evaluation component."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from typing import Any

from component_catalog import COMPONENT_NAMES
from component_runner import run_component
from components import build_component_config
from config import resolve_backends
from datasets import DatasetConfig
from settings import EvalSettings, get_settings
from themefinder.llm import OpenAILLM
from utils import gateway
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _create_default_llm(settings: EvalSettings) -> OpenAILLM:
    """Build the default task model from one consistent settings snapshot."""
    base_url, api_key = gateway.gateway_credentials(settings=settings)
    return OpenAILLM(
        model=settings.auto_eval_model,
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
    context: Any | None = None,
    question_num: int | None = None,
    settings: EvalSettings | None = None,
) -> dict[str, Any]:
    """Build and run one component through the configured framework backends."""
    if component not in COMPONENT_NAMES:
        raise ValueError(
            f"Unknown component '{component}'. Must be one of: {list(COMPONENT_NAMES)}"
        )

    settings = settings if settings is not None else get_settings()
    task_llm = llm if llm is not None else _create_default_llm(settings)
    if component == "mapping" and judge_llm is not None:
        logger.warning(
            "judge_llm is ignored for mapping because it has no judge evaluator"
        )
    evaluator_llm = judge_llm if judge_llm is not None else task_llm
    dataset_config = DatasetConfig(dataset=dataset, component=component)
    component_config = build_component_config(
        component,
        judge_llm=evaluator_llm,
        question_num=question_num,
    )
    backends = resolve_backends(
        dataset_config,
        settings=settings,
        context=context,
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
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    results = asyncio.run(
        evaluate_component(
            component=args.component,
            dataset=args.dataset,
            question_num=args.question,
        )
    )
    print(json.dumps(results, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
