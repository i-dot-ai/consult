"""Sweep distance_threshold / min_coverage for build_consensus_gt.py's clustering step.

Four modes:
  - Multiple values for either param (default): prints a grid of surviving
    cluster counts per combination across all questions (or the one given via
    --question), then asks whether to zoom in with a finer sweep around the
    best-found combination. Repeats until you decline.
  - Exactly one value for both params: prints full cluster membership and
    dropped themes for that combination (no refinement loop).
  - --interactive: steps through every (question, distance_threshold,
    min_coverage) combination one at a time, showing full cluster
    membership and dropped themes, pausing between each so you can eyeball
    whether genuine paraphrases are merging without distinct themes being
    lumped together.
  - --llm-as-judge: for a fixed min_coverage, sweeps every distance_threshold,
    uses an LLM to review each resulting cluster and remove outlier themes
    that don't belong, rechecks min_coverage on what's left, then picks the
    distance_threshold with the most surviving clusters and writes it as the
    final consensus (same output path as build_consensus_gt.py).

Reuses (and populates) the same embeddings cache as build_consensus_gt.py,
so running this before/after build_consensus_gt.py avoids re-fetching
embeddings.

Usage:
  # Broad sweep — just the counts; loops to let you zoom in
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

  # Let an LLM prune outliers and pick the best distance_threshold, then write the consensus
  python sweep_consensus_params.py <gt_dir> --llm-as-judge \\
      --distance-thresholds 0.05,0.10,0.15,0.20,0.25 \\
      --min-coverages 0.5
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from openai import OpenAI
from pydantic import BaseModel, Field

from build_consensus_gt import (
    DEFAULT_MODEL,
    EMBEDDING_MODEL,
    assemble_consensus_themes,
    cluster_themes,
    fetch_embeddings,
    load_all_runs,
    make_client,
    synthesise_labels,
    write_consensus,
)

JUDGE_SYSTEM_PROMPT = """You are reviewing clusters of consultation themes that were grouped automatically by embedding similarity. Similarity-based clustering sometimes lumps together themes that use similar wording but make a different substantive point.

For each cluster below, identify any member theme(s) that are outliers -- i.e. they do not share the same substantive point as the majority of the cluster -- and should be removed. Most clusters will have zero outliers; only flag a member when you are confident it doesn't belong.

Return one entry per cluster (using the cluster_index shown in its heading), with the 1-based indices of any outlier members. Use an empty list when no outliers are found."""


class ClusterOutlierReview(BaseModel):
    cluster_index: int = Field(description="1-based cluster number, matching the heading in the prompt")
    outlier_member_indices: list[int] = Field(
        description="1-based indices of themes within this cluster that do not share the same "
        "substantive point as the rest and should be removed. Empty list if every member belongs."
    )


class OutlierReviewResponse(BaseModel):
    clusters: list[ClusterOutlierReview]


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
    total_themes = len(themes_with_runs)
    print(f"\n{question} ({total_themes} themes across {total_runs} runs)")
    header = "  distance_threshold \\ min_coverage | " + " | ".join(f"{mc:.2f}" for mc in min_coverages)
    print(header)
    print("  " + "-" * (len(header) - 2))
    label_width = 33
    for dt in distance_thresholds:
        all_clusters = [
            cluster_themes(themes_with_runs, embeddings, total_runs, dt, mc)
            for mc in min_coverages
        ]
        n_clusters  = [len(c) for c in all_clusters]
        kept        = [sum(len(m) for m, _ in c) for c in all_clusters]
        dropped     = [total_themes - k for k in kept]

        print(f"  {f'{dt:.2f}  clusters':<{label_width}} | " + " | ".join(f"{v:>4}" for v in n_clusters))
        print(f"  {f'kept':<{label_width}} | " + " | ".join(f"{v:>4}" for v in kept))
        print(f"  {f'dropped':<{label_width}} | " + " | ".join(f"{v:>4}" for v in dropped))
        print()


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


def judge_cluster_outliers(
    clusters: list[tuple[list[tuple[dict, int]], float]],
    question: str,
    client: OpenAI,
    model: str,
) -> list[list[tuple[dict, int]]]:
    """Ask the LLM to flag outlier members within each cluster. Returns pruned member lists
    in the same order as `clusters`; single-member clusters pass through unreviewed."""
    reviewable = [(i, members) for i, (members, _) in enumerate(clusters) if len(members) > 1]
    if not reviewable:
        return [members for members, _ in clusters]

    cluster_blocks = []
    for i, members in reviewable:
        theme_lines = "\n".join(
            f"  {j}. {t['topic_label']}: {t['topic_description']}" for j, (t, _) in enumerate(members, 1)
        )
        cluster_blocks.append(f"## Cluster {i + 1}\n{theme_lines}")

    human_prompt = (
        f"Question: {question}\n\n"
        + "\n\n".join(cluster_blocks)
        + f"\n\nReview each of the {len(reviewable)} cluster(s) above for outlier members."
    )

    result = (
        client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": human_prompt},
            ],
            response_format=OutlierReviewResponse,
        )
        .choices[0]
        .message.parsed
    )
    outliers_by_cluster = {
        review.cluster_index - 1: set(review.outlier_member_indices) for review in result.clusters
    }

    return [
        [m for j, m in enumerate(members, 1) if j not in outliers_by_cluster.get(i, set())]
        for i, (members, _) in enumerate(clusters)
    ]


def apply_min_coverage(
    pruned_members: list[list[tuple[dict, int]]],
    total_runs: int,
    min_coverage: float,
) -> list[tuple[list[tuple[dict, int]], float]]:
    """Recompute coverage after pruning and drop clusters that fall below min_coverage."""
    surviving = []
    for members in pruned_members:
        if not members:
            continue
        coverage = len({run_num for _, run_num in members}) / total_runs
        if coverage >= min_coverage:
            surviving.append((members, coverage))
    return sorted(surviving, key=lambda x: -x[1])


def select_best_distance_threshold(
    question: str,
    themes_with_runs: list[tuple[dict, int]],
    embeddings: np.ndarray,
    total_runs: int,
    distance_thresholds: list[float],
    min_coverage: float,
    client: OpenAI,
    model: str,
) -> tuple[float, list[tuple[list[tuple[dict, int]], float]]]:
    """Try each distance_threshold, use the LLM to prune outliers from the resulting clusters,
    recheck min_coverage, and return the threshold that keeps the most themes. Ties are broken
    by cluster count; any remaining tie favours the smallest/strictest threshold."""
    best_dt = distance_thresholds[0]
    best_clusters: list[tuple[list[tuple[dict, int]], float]] = []
    best_score = (-1, -1)
    total_themes = len(themes_with_runs)

    for dt in distance_thresholds:
        raw_clusters = cluster_themes(themes_with_runs, embeddings, total_runs, dt, min_coverage)
        pruned_members = judge_cluster_outliers(raw_clusters, question, client, model)
        surviving = apply_min_coverage(pruned_members, total_runs, min_coverage)
        outliers_removed = sum(len(m) for m, _ in raw_clusters) - sum(len(m) for m in pruned_members)
        kept = sum(len(m) for m, _ in surviving)
        dropped = total_themes - kept
        print(
            f"  distance_threshold={dt:.2f} → {len(raw_clusters)} cluster(s) before review, "
            f"{outliers_removed} outlier theme(s) removed, {len(surviving)} cluster(s) survive "
            f"min_coverage ({kept} theme(s) kept, {dropped} theme(s) dropped)"
        )
        score = _clustering_score(kept, len(surviving))
        if score > best_score:
            best_score = score
            best_dt = dt
            best_clusters = surviving

    return best_dt, best_clusters




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


def _clustering_score(kept: int, n_clusters: int) -> tuple[int, int]:
    """Ranking key: maximise cluster count, break ties by themes kept."""
    return (n_clusters, kept)


def find_best_params(
    themes_with_runs: list[tuple[dict, int]],
    embeddings: np.ndarray,
    distance_thresholds: list[float],
    min_coverages: list[float],
) -> tuple[float, float]:
    """Return the (distance_threshold, min_coverage) with the highest _clustering_score."""
    total_runs = len({run for _, run in themes_with_runs})
    best_score = (-1, -1)
    best_dt, best_mc = distance_thresholds[0], min_coverages[0]
    for dt in distance_thresholds:
        for mc in min_coverages:
            clusters = cluster_themes(themes_with_runs, embeddings, total_runs, dt, mc)
            score = _clustering_score(sum(len(m) for m, _ in clusters), len(clusters))
            if score > best_score:
                best_score = score
                best_dt, best_mc = dt, mc
    return best_dt, best_mc


def suggest_finer_range(
    best_dt: float,
    distance_thresholds: list[float],
    best_mc: float,
    min_coverages: list[float],
) -> tuple[list[float], list[float]]:
    """Generate a finer grid centred on (best_dt, best_mc), using 1/5 of the original step size."""

    def finer(values: list[float], best: float) -> list[float]:
        step = min(abs(values[i + 1] - values[i]) for i in range(len(values) - 1)) if len(values) > 1 else 0.05
        new_step = round(step / 5, 6)
        lo = round(max(0.0, best - step), 6)
        hi = round(min(1.0, best + step), 6)
        n = round((hi - lo) / new_step)
        return [round(lo + i * new_step, 4) for i in range(n + 1)]

    return finer(distance_thresholds, best_dt), finer(min_coverages, best_mc)


def sweep(
    gt_dir: Path,
    distance_thresholds: list[float],
    min_coverages: list[float],
    question_filter: str | None,
    interactive: bool,
    llm_as_judge: bool,
    model: str,
) -> None:
    if not gt_dir.is_dir():
        print(f"Directory not found: {gt_dir}", file=sys.stderr)
        sys.exit(1)

    if llm_as_judge and interactive:
        print("--llm-as-judge and --interactive are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    if llm_as_judge and len(min_coverages) != 1:
        print(
            "--llm-as-judge picks a single distance_threshold for a target min_coverage, "
            "so pass exactly one --min-coverages value.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = make_client()
    cache_path = gt_dir / f".embeddings_cache_consensus_{EMBEDDING_MODEL}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

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

        # Pre-fetch embeddings for all questions once (reused across refinement loop iterations).
        embeddings_by_question: dict[str, np.ndarray] = {}
        for question, themes_with_runs in sorted(by_question.items()):
            texts = [t["topic_description"] for t, _ in themes_with_runs]
            embeddings_by_question[question] = fetch_embeddings(texts, client, cache)

        for question, themes_with_runs in sorted(by_question.items()):
            total_runs = len({run_num for _, run_num in themes_with_runs})
            embeddings = embeddings_by_question[question]
            cur_dts = list(distance_thresholds)
            cur_mcs = list(min_coverages)
            best_clusters: list[tuple[list[tuple[dict, int]], float]] = []
            best_dt = cur_dts[0]

            while True:
                if llm_as_judge:
                    min_coverage = cur_mcs[0]
                    print(
                        f"\n{question} ({len(themes_with_runs)} themes across {total_runs} runs, "
                        f"min_coverage={min_coverage:.2f}): sweeping distance thresholds with LLM-as-judge review"
                    )
                    best_dt, best_clusters = select_best_distance_threshold(
                        question, themes_with_runs, embeddings, total_runs,
                        cur_dts, min_coverage, client, model,
                    )
                    new_dts, _ = suggest_finer_range(best_dt, cur_dts, best_dt, cur_mcs)
                    print(f"\nBest combination for {question}: distance_threshold={best_dt:.4f}")
                    print(f"Suggested finer sweep:  distance_thresholds={','.join(f'{x:.4f}' for x in new_dts)}")
                else:
                    show_detail = len(cur_dts) == 1 and len(cur_mcs) == 1
                    if show_detail:
                        print_detail(question, themes_with_runs, embeddings, total_runs, cur_dts[0], cur_mcs[0])
                        break
                    print_grid(question, themes_with_runs, embeddings, total_runs, cur_dts, cur_mcs)
                    best_dt, best_mc = find_best_params(themes_with_runs, embeddings, cur_dts, cur_mcs)
                    new_dts, new_mcs = suggest_finer_range(best_dt, cur_dts, best_mc, cur_mcs)
                    print(
                        f"\nBest combination for {question}: "
                        f"distance_threshold={best_dt:.4f}, min_coverage={best_mc:.4f}"
                    )
                    print(
                        f"Suggested finer sweep:  distance_thresholds={','.join(f'{x:.4f}' for x in new_dts)}\n"
                        f"                        min_coverages={','.join(f'{x:.4f}' for x in new_mcs)}"
                    )

                try:
                    choice = input("\nRun a more granular sweep around these values? [y/n]: ").strip().lower()
                except EOFError:
                    break

                if choice != "y":
                    break

                cur_dts = new_dts
                if not llm_as_judge:
                    cur_mcs = new_mcs

            if llm_as_judge and best_clusters:
                kept = sum(len(m) for m, _ in best_clusters)
                dropped = len(themes_with_runs) - kept
                print(
                    f"  selected distance_threshold={best_dt:.4f} → {len(best_clusters)} consensus cluster(s), "
                    f"{kept} theme(s) kept, {dropped} theme(s) dropped"
                )
                representatives = synthesise_labels(best_clusters, question, client, model)
                consensus_themes = assemble_consensus_themes(best_clusters, representatives)
                out_path = write_consensus(gt_dir, question, consensus_themes)
                print(f"  {len(consensus_themes)} consensus theme(s) → {out_path}")

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
    parser.add_argument(
        "--llm-as-judge", action="store_true",
        help="For each distance_threshold, use an LLM to review every cluster and remove "
             "outlier themes that don't belong, then recheck min_coverage. Picks the "
             "distance_threshold with the most surviving clusters and writes it as the final "
             "consensus (same output path as build_consensus_gt.py). Requires exactly one "
             "--min-coverages value; mutually exclusive with --interactive.",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"LLM model used for outlier review and label synthesis with --llm-as-judge (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    sweep(
        args.gt_dir, args.distance_thresholds, args.min_coverages, args.question,
        args.interactive, args.llm_as_judge, args.model,
    )
