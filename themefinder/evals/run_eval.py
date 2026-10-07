"""Command-line entry point for a single ThemeFinder evaluation component."""

import argparse
import asyncio
import json
from collections.abc import Sequence

from component_catalog import COMPONENT_NAMES
from evaluation import evaluate_component


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
