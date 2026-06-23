"""Sweep distance_threshold / min_coverage for build_consensus_gt.py's clustering step.

Three modes:
  - Multiple values for either param (default): prints a grid of surviving
    cluster counts per combination, so you can spot where the count
    stabilises.
  - Exactly one value for both params: prints full cluster membership and
    dropped themes for that combination.
  - --interactive: steps through every (question, distance_threshold,
    min_coverage) combination one at a time, showing full cluster
    membership and dropped themes, pausing between each so you can eyeball
    whether genuine paraphrases are merging without distinct themes being
    lumped together.

Reuses (and populates) the same embeddings cache as build_consensus_gt.py,
so running this before/after build_consensus_gt.py avoids re-fetching
embeddings.

Usage:
  # Broad sweep — just the counts
  python sweep_consensus_params.py <gt_dir> \\
      --distance-thresholds 0.05,0.10,0.15,0.20,0.25 \\
      --min-coverages 0.4,0.5,0.6,0.8

  # Narrow down on one question
  python sweep_consensus_params.py <gt_dir> \\
      --distance-thresholds 0.15 --min-coverages 0.5 \\
      --question question_part_1

  # Step through every combination interactively
  python sweep_consensus_params.py <gt_dir> --interactive \\
      --distance-thresholds 0.05,0.10,0.15,0.20,0.25 \\
      --min-coverages 0.4,0.5,0.6,0.8
"""

import argparse
import json
import sys
from pathlib import Path

from build_consensus_gt import (
    EMBEDDING_MODEL,
    cluster_themes,
    fetch_embeddings,
    load_all_runs,
    make_client,
)


def parse_float_list(raw: str) -> list[float]:
    return [float(x) for x in raw.split(",")]


def print_grid(
    question: str,
    themes_with_runs: list[tuple[dict, int]],
    embeddings,
    total_runs: int,
    distance_thresholds: list[float],
    min_coverages: list[float],
) -> None:
    print(f"\n{question} ({len(themes_with_runs)} themes across {total_runs} runs)")
    header = "  distance_threshold \\ min_coverage | " + " | ".join(f"{mc:.2f}" for mc in min_coverages)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for dt in distance_thresholds:
        counts = [
            len(cluster_themes(themes_with_runs, embeddings, total_runs, dt, mc))
            for mc in min_coverages
        ]
        row = " | ".join(f"{c:>4}" for c in counts)
        print(f"  {dt:<33.2f} | {row}")


def find_dropped(
    themes_with_runs: list[tuple[dict, int]],
    clusters: list[tuple[list[tuple[dict, int]], float]],
) -> list[tuple[dict, int]]:
    """Themes that didn't survive into any cluster above min_coverage."""
    covered = {id(member) for members, _ in clusters for member in members}
    return [t for t in themes_with_runs if id(t) not in covered]


def print_detail(
    question: str,
    themes_with_runs: list[tuple[dict, int]],
    embeddings,
    total_runs: int,
    distance_threshold: float,
    min_coverage: float,
) -> None:
    clusters = cluster_themes(themes_with_runs, embeddings, total_runs, distance_threshold, min_coverage)
    dropped = find_dropped(themes_with_runs, clusters)
    print(
        f"\n{question}: distance_threshold={distance_threshold} min_coverage={min_coverage} "
        f"→ {len(clusters)} cluster(s) surviving, {len(dropped)} theme(s) dropped\n"
    )
    print("  Surviving clusters:")
    for i, (members, coverage) in enumerate(clusters, 1):
        distinct_runs = len({run_num for _, run_num in members})
        print(f"\n  Cluster {i} (coverage={coverage:.2f}, {distinct_runs}/{total_runs} runs, {len(members)} theme(s)):")
        for theme, run_num in members:
            print(f"    [run {run_num}] {theme['topic_label']}: {theme['topic_description']}")

    if dropped:
        print("\n  Dropped (below min_coverage):")
        for theme, run_num in dropped:
            print(f"    [run {run_num}] {theme['topic_label']}: {theme['topic_description']}")
    print()


def interactive_walkthrough(
    by_question: dict[str, list[tuple[dict, int]]],
    client,
    cache: dict[str, list[float]],
    distance_thresholds: list[float],
    min_coverages: list[float],
) -> None:
    combos = [(dt, mc) for dt in distance_thresholds for mc in min_coverages]
    questions = sorted(by_question.items())
    total = len(questions) * len(combos)
    step = 0

    for question, themes_with_runs in questions:
        total_runs = len({run_num for _, run_num in themes_with_runs})
        texts = [t["topic_description"] for t, _ in themes_with_runs]
        embeddings = fetch_embeddings(texts, client, cache)

        for dt, mc in combos:
            step += 1
            print_detail(question, themes_with_runs, embeddings, total_runs, dt, mc)
            if step == total:
                return
            choice = input(f"[{step}/{total}] Enter for next combination, 'q' to quit: ").strip().lower()
            if choice == "q":
                return


def sweep(
    gt_dir: Path,
    distance_thresholds: list[float],
    min_coverages: list[float],
    question_filter: str | None,
    interactive: bool,
) -> None:
    if not gt_dir.is_dir():
        print(f"Directory not found: {gt_dir}", file=sys.stderr)
        sys.exit(1)

    client = make_client()
    cache_path = gt_dir / f".embeddings_cache_consensus_{EMBEDDING_MODEL}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    show_detail = len(distance_thresholds) == 1 and len(min_coverages) == 1

    try:
        by_question = load_all_runs(gt_dir)
        if question_filter:
            by_question = {q: v for q, v in by_question.items() if q == question_filter}
            if not by_question:
                print(f"Question '{question_filter}' not found.", file=sys.stderr)
                sys.exit(1)

        if interactive:
            interactive_walkthrough(by_question, client, cache, distance_thresholds, min_coverages)
            return

        for question, themes_with_runs in sorted(by_question.items()):
            total_runs = len({run_num for _, run_num in themes_with_runs})
            texts = [t["topic_description"] for t, _ in themes_with_runs]
            embeddings = fetch_embeddings(texts, client, cache)

            if show_detail:
                print_detail(
                    question, themes_with_runs, embeddings, total_runs,
                    distance_thresholds[0], min_coverages[0],
                )
            else:
                print_grid(
                    question, themes_with_runs, embeddings, total_runs,
                    distance_thresholds, min_coverages,
                )
    finally:
        cache_path.write_text(json.dumps(cache))
        print(f"\nEmbedding cache saved to {cache_path}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sweep distance_threshold/min_coverage for build_consensus_gt.py's clustering."
    )
    parser.add_argument("gt_dir", type=Path, help="Path to the GT directory containing run_* subdirectories")
    parser.add_argument(
        "--distance-thresholds", type=parse_float_list, default=[0.05, 0.10, 0.15, 0.20, 0.25],
        help="Comma-separated cosine distance thresholds to try (default: 0.05,0.10,0.15,0.20,0.25)",
    )
    parser.add_argument(
        "--min-coverages", type=parse_float_list, default=[0.4, 0.5, 0.6, 0.8],
        help="Comma-separated min_coverage fractions to try (default: 0.4,0.5,0.6,0.8)",
    )
    parser.add_argument("--question", default=None, help="Restrict to a single question_part_N (default: all)")
    parser.add_argument(
        "--interactive", action="store_true",
        help="Step through every (question, distance_threshold, min_coverage) combination, "
             "pausing after each to show full cluster membership and dropped themes",
    )
    args = parser.parse_args()

    sweep(args.gt_dir, args.distance_thresholds, args.min_coverages, args.question, args.interactive)
