"""Run theme finding on one question of a local eval dataset.

Why: a quick way to see what the concept-based method (or the original pipeline, for
comparison) produces, and to tune the concept settings, without the full scored eval harness.

Usage, from themefinder/evals:
    uv run --extra eval python run_concept_themes.py --dataset gambling_XS --question question_part_1
    uv run --extra eval python run_concept_themes.py --method baseline
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from settings import eval_settings
from themefinder.llm import OpenAIEmbedder, OpenAILLM
from utils import gateway

from themefinder import (
    ConceptClusteringConfig,
    find_themes_via_concepts,
    theme_condensation,
    theme_generation,
    theme_refinement,
)

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "benchmark_results" / "theme_runs"


def load_question(dataset: str, question_part: str) -> tuple[str, pd.DataFrame]:
    """Load question text and responses (response_id, response) from a local dataset."""
    question_dir = DATA_DIR / dataset / "inputs" / question_part
    question = json.loads((question_dir / "question.json").read_text())["question_text"]
    responses = pd.read_json(question_dir / "responses.jsonl", lines=True)
    return question, responses[["response_id", "response"]]


async def run_concepts(args, llm, base_url, api_key, question, responses) -> dict:
    """Concept-based method; returns themes plus concepts and outliers for inspection."""
    embedder = OpenAIEmbedder(
        model=args.embedding_model, base_url=base_url, api_key=api_key
    )
    config = ConceptClusteringConfig(
        distance_threshold=args.distance_threshold,
        min_cluster_size=args.min_cluster_size,
        leftover_target_fraction=args.leftover_target_fraction,
        max_review_rounds=args.max_review_rounds,
    )
    result = await find_themes_via_concepts(
        responses, llm, embedder, question, config=config, concurrency=args.concurrency
    )
    concepts, outliers = result["concepts"], result["outliers"]
    summary = (
        f"{len(result['themes'])} themes from {len(concepts)} concepts; "
        f"{len(outliers)} outliers ({len(outliers) / max(len(concepts), 1):.0%})"
    )
    return {
        "themes": result["themes"],
        "concepts": concepts,
        "outliers": outliers,
        "summary": summary,
    }


async def run_baseline(args, llm, question, responses) -> dict:
    """Original generation -> condensation -> refinement, as the eval harness runs it."""
    themes_df, _ = await theme_generation(
        responses, llm, question=question, concurrency=args.concurrency
    )
    condensed_df, _ = await theme_condensation(
        themes_df, llm, question=question, concurrency=args.concurrency
    )
    refined_df, _ = await theme_refinement(
        condensed_df, llm, question=question, concurrency=args.concurrency
    )
    return {"themes": refined_df, "summary": f"{len(refined_df)} themes"}


async def main(args: argparse.Namespace) -> None:
    base_url, api_key = gateway.gateway_credentials()
    model = args.model or eval_settings.auto_eval_model
    if not model:
        raise RuntimeError("Pass --model or set AUTO_EVAL_MODEL")

    llm = OpenAILLM(
        model=model,
        request_kwargs={"temperature": 0},
        base_url=base_url,
        api_key=api_key,
    )

    question, responses = load_question(args.dataset, args.question)
    if args.limit:
        responses = responses.head(args.limit)
    print(
        f"Question: {question}\nResponses: {len(responses)}  "
        f"Method: {args.method}  Model: {model}\n"
    )

    if args.method == "concepts":
        result = await run_concepts(args, llm, base_url, api_key, question, responses)
    else:
        result = await run_baseline(args, llm, question, responses)

    print("\nTHEMES")
    for row in result["themes"].itertuples():
        print(f"  {row.topic_id} ({row.source_topic_count} responses): {row.topic}")
    print(f"\n{result['summary']}")

    run_dir = (
        OUTPUT_DIR
        / datetime.now().strftime("%Y%m%d_%H%M%S")
        / f"{args.dataset}_{args.question}_{args.method}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    saved = [name for name in ("themes", "concepts", "outliers") if name in result]
    for name in saved:
        result[name].to_csv(run_dir / f"{name}.csv", index=False)
    print(f"Saved {', '.join(f'{n}.csv' for n in saved)} to {run_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dataset", default="gambling_XS")
    parser.add_argument("--question", default="question_part_1")
    parser.add_argument(
        "--method",
        choices=("concepts", "baseline"),
        default="concepts",
        help="concepts = new method; baseline = original generation/condensation/refinement",
    )
    parser.add_argument("--model", help="Chat model (defaults to AUTO_EVAL_MODEL)")
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-large",
        help="Concepts method only",
    )
    parser.add_argument("--limit", type=int, help="Only use the first N responses")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--distance-threshold", type=float, default=0.45)
    parser.add_argument("--min-cluster-size", type=int, default=3)
    parser.add_argument("--leftover-target-fraction", type=float, default=0.05)
    parser.add_argument("--max-review-rounds", type=int, default=5)
    asyncio.run(main(parser.parse_args()))
