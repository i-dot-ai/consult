"""Analyse theme similarity between comparison datasets and two ground truth datasets.

Ground truths are loaded from their consensus/ subdirectory (built by build_consensus_gt.py).
For each test dataset, analysis is run across all run_* subdirectories and results are
aggregated to mean ± std of the proportion of themes assigned to each GT group.

For each question per run:
  1. Embeds all themes via a text embedding model.
  2. Computes a centroid and mean distance from centroid for each GT group.
  3. For each test theme, computes a normalised distance to each GT cluster and
     performs k-NN (default k=5) across both groups.
     Themes where distances are within 10% of each other, or kNN votes differ by at most 1,
     are classified as 'both' (overlapping themes present in both groups).
  4. Writes per-run detail to log files; prints a mean±std summary table to stdout.

Expected directory structure:
  <search_dir>/
    <gt1_name>/consensus/question_part_<N>/clustered_themes.json
    <gt2_name>/consensus/question_part_<N>/clustered_themes.json
    [<test_name>/]<dataset_name>/run_<N>/question_part_<N>/clustered_themes.json

If test_dir is omitted, all directories in search_dir other than the two GT dirs are analysed.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
import plotly.graph_objects as go
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.home() / "Code" / "consult" / ".env")

EMBEDDING_MODEL = "text-embedding-3-large-sweden"
DEFAULT_K = 5
NORM_BOTH_THRESHOLD = 0.9  # min(d1,d2)/max(d1,d2) above this → 'both'


def natural_sort_key(name: str) -> list:
    """Sort key that orders embedded numbers numerically, e.g. dwp_9 before dwp_10."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def dataset_sort_key(name: str, order: list[int] | None) -> tuple:
    """Sort key placing datasets in an explicit numeric order (matched against the first integer
    found in the dataset name), falling back to natural sort for anything not in `order`."""
    if order:
        match = re.search(r"\d+", name)
        number = int(match.group()) if match else None
        if number in order:
            return (0, order.index(number))
    return (1, natural_sort_key(name))


@dataclass
class AggStats:
    """Aggregated proportions (0–100) across runs for one dataset+question."""
    norm_gt1_mean: float; norm_gt1_std: float
    norm_gt2_mean: float; norm_gt2_std: float
    norm_both_mean: float; norm_both_std: float
    knn_gt1_mean: float;  knn_gt1_std: float
    knn_gt2_mean: float;  knn_gt2_std: float
    knn_both_mean: float; knn_both_std: float
    # Inclusive variants: themes counted as "both" are folded into each overlapping group.
    norm_g1_inc_both_mean: float; norm_g1_inc_both_std: float
    norm_g2_inc_both_mean: float; norm_g2_inc_both_std: float
    knn_g1_inc_both_mean: float;  knn_g1_inc_both_std: float
    knn_g2_inc_both_mean: float;  knn_g2_inc_both_std: float
    themes_mean: float;   themes_std: float
    n_runs: int


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        http_client=httpx.Client(verify=False),
    )


def load_themes(path: Path) -> list[dict]:
    try:
        with path.open() as f:
            return json.load(f)["theme_nodes"]
    except json.decoder.JSONDecodeError as e:
        print(f'Problem loading {path}')
        raise e

def fetch_embeddings(texts: list[str], client: OpenAI, cache: dict[str, list[float]]) -> list[np.ndarray]:
    missing = [t for t in texts if t not in cache]
    if missing:
        print(f"  Fetching {len(missing)} embedding(s)...", file=sys.stderr)
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=missing)
        for text, item in zip(missing, response.data):
            cache[text] = item.embedding
    return [np.array(cache[t]) for t in texts]


def cluster_stats(embeddings: list[np.ndarray]) -> tuple[np.ndarray, float]:
    centroid = np.mean(embeddings, axis=0)
    dists = [float(np.linalg.norm(e - centroid)) for e in embeddings]
    return centroid, float(np.mean(dists))


def normalised_distance(embedding: np.ndarray, centroid: np.ndarray, mean_dist: float) -> float:
    dist = float(np.linalg.norm(embedding - centroid))
    return dist / mean_dist if mean_dist > 0 else dist


def knn_group(embedding: np.ndarray, gt1_embeddings: list[np.ndarray], gt2_embeddings: list[np.ndarray], k: int) -> tuple[str, int, int]:
    neighbours = (
        [(float(np.linalg.norm(embedding - e)), "1") for e in gt1_embeddings]
        + [(float(np.linalg.norm(embedding - e)), "2") for e in gt2_embeddings]
    )
    top_k = sorted(neighbours, key=lambda x: x[0])[:k]
    gt1_votes = sum(1 for _, g in top_k if g == "1")
    gt2_votes = k - gt1_votes
    if min(gt1_votes, gt2_votes) >= k // 2:
        return "both", gt1_votes, gt2_votes
    return ("1" if gt1_votes >= gt2_votes else "2"), gt1_votes, gt2_votes


def norm_group_assign(d1: float, d2: float, both_threshold: float = NORM_BOTH_THRESHOLD) -> str:
    if max(d1, d2) > 0 and min(d1, d2) / max(d1, d2) > both_threshold:
        return "both"
    return "1" if d1 <= d2 else "2"


def load_themes_by_question(root: Path, run: str) -> dict[str, list[dict]]:
    """Load themes for a given run subdirectory name (e.g. 'consensus', 'run_1')."""
    if not root.is_dir():
        raise FileNotFoundError(f'{root} does not exist, themes cannot be loaded')

    result: dict[str, list[dict]] = {}
    for path in sorted(root.rglob("clustered_themes.json")):
        if run not in path.parts:
            continue
        result[path.parent.name] = load_themes(path)
    return result


def load_runs(dataset_dir: Path) -> dict[int, dict[str, list[dict]]]:
    """Return {run_num: {question: themes}} for all run_* subdirs of dataset_dir."""
    runs: dict[int, dict[str, list[dict]]] = {}
    for run_dir in sorted(dataset_dir.rglob("run_*")):
        if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
            continue
        try:
            run_num = int(run_dir.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        themes_by_q: dict[str, list[dict]] = {}
        for path in sorted(run_dir.rglob("clustered_themes.json")):
            themes_by_q[path.parent.name] = load_themes(path)
        if themes_by_q:
            runs[run_num] = themes_by_q
    return runs


def aggregate(run_counts: list[tuple[int, int, int, int, int, int]]) -> AggStats:
    """Convert per-run count tuples to mean±std proportions across runs."""
    rows = []
    for n1, n2, nb, k1, k2, kb in run_counts:
        total_n = n1 + n2 + nb
        total_k = k1 + k2 + kb
        if total_n == 0 or total_k == 0:
            continue
        rows.append([
            100 * n1 / total_n, 100 * n2 / total_n, 100 * nb / total_n,
            100 * k1 / total_k, 100 * k2 / total_k, 100 * kb / total_k,
            100 * (n1 + nb) / total_n, 100 * (n2 + nb) / total_n,
            100 * (k1 + kb) / total_k, 100 * (k2 + kb) / total_k,
            total_n,
        ])
    arr = np.array(rows)
    m = arr.mean(axis=0)
    s = arr.std(axis=0) if len(rows) > 1 else np.zeros(arr.shape[1])
    return AggStats(
        norm_gt1_mean=m[0], norm_gt1_std=s[0],
        norm_gt2_mean=m[1], norm_gt2_std=s[1],
        norm_both_mean=m[2], norm_both_std=s[2],
        knn_gt1_mean=m[3],  knn_gt1_std=s[3],
        knn_gt2_mean=m[4],  knn_gt2_std=s[4],
        knn_both_mean=m[5], knn_both_std=s[5],
        norm_g1_inc_both_mean=m[6], norm_g1_inc_both_std=s[6],
        norm_g2_inc_both_mean=m[7], norm_g2_inc_both_std=s[7],
        knn_g1_inc_both_mean=m[8],  knn_g1_inc_both_std=s[8],
        knn_g2_inc_both_mean=m[9],  knn_g2_inc_both_std=s[9],
        themes_mean=m[10],   themes_std=s[10],
        n_runs=len(rows),
    )


def analyse_dataset(
    dataset_name: str,
    themes_by_question: dict[str, list[dict]],
    questions: list[str],
    gt1_name: str,
    gt2_name: str,
    gt1_embs_by_q: dict[str, list[np.ndarray]],
    gt2_embs_by_q: dict[str, list[np.ndarray]],
    gt1_stats_by_q: dict[str, tuple[np.ndarray, float]],
    gt2_stats_by_q: dict[str, tuple[np.ndarray, float]],
    client: OpenAI,
    cache: dict[str, list[float]],
    log_path: Path,
    k: int = DEFAULT_K,
    norm_both_threshold: float = NORM_BOTH_THRESHOLD,
) -> dict[str, tuple[int, int, int, int, int, int]]:
    """Run analysis for one dataset/run. Writes detail to log_path.
    Returns {question: (norm_gt1, norm_gt2, norm_both, knn_gt1, knn_gt2, knn_both)}."""

    results: dict[str, tuple[int, int, int, int, int, int]] = {}

    with log_path.open("w") as log:
        def out(line: str = "") -> None:
            log.write(line + "\n")

        out(f"Analysis: {dataset_name}")
        out("=" * 60)

        for question in questions:
            if question not in themes_by_question:
                out(f"\n{question}: not found in this dataset, skipping.")
                continue

            gt1_embeddings = gt1_embs_by_q[question]
            gt2_embeddings = gt2_embs_by_q[question]
            gt1_centroid, gt1_mean = gt1_stats_by_q[question]
            gt2_centroid, gt2_mean = gt2_stats_by_q[question]

            out(f"\n{question}")
            out("-" * 40)
            out(f"  {gt1_name}: mean dist from centroid={gt1_mean:.4f} ({len(gt1_embeddings)} themes)")
            out(f"  {gt2_name}: mean dist from centroid={gt2_mean:.4f} ({len(gt2_embeddings)} themes)")

            themes = themes_by_question[question]
            theme_texts = [t["topic_description"] for t in themes]
            theme_embeddings = fetch_embeddings(theme_texts, client, cache)
            labels = [chr(ord("A") + i) for i in range(len(themes))]

            g1_label = f"Norm({gt1_name[:8]})"
            g2_label = f"Norm({gt2_name[:8]})"
            header = f"  Theme | {g1_label} | {g2_label} | Norm Grp | Votes | kNN Grp"
            out(f"\n{header}")
            out("  " + "-" * (len(header) - 2))

            norm_gt1 = norm_gt2 = norm_both = knn_gt1 = knn_gt2 = knn_both = 0
            for label, theme, emb in zip(labels, themes, theme_embeddings):
                d1 = normalised_distance(emb, gt1_centroid, gt1_mean)
                d2 = normalised_distance(emb, gt2_centroid, gt2_mean)
                norm_group = norm_group_assign(d1, d2, norm_both_threshold)
                knn_winner, v1, v2 = knn_group(emb, gt1_embeddings, gt2_embeddings, k)
                out(f"  {label:<5} | {d1:.3f}      | {d2:.3f}      | {norm_group:^8} | {v1}-{v2:<4} | {knn_winner:^8}")
                if norm_group == "1": norm_gt1 += 1
                elif norm_group == "2": norm_gt2 += 1
                else: norm_both += 1
                if knn_winner == "1": knn_gt1 += 1
                elif knn_winner == "2": knn_gt2 += 1
                else: knn_both += 1

            out()
            for label, text in zip(labels, theme_texts):
                out(f"  {label}: {text}")

            results[question] = (norm_gt1, norm_gt2, norm_both, knn_gt1, knn_gt2, knn_both)

    return results


def pct_to_count(pct_mean: float, pct_std: float, themes_mean: float) -> tuple[float, float]:
    """Convert an aggregated percentage (mean±std, 0-100) back to a theme count, scaled by the
    dataset's mean number of themes per run, so it's directly comparable to consensus group sizes."""
    return pct_mean / 100 * themes_mean, pct_std / 100 * themes_mean


def fmt_count(pct_mean: float, pct_std: float, themes_mean: float, width: int) -> str:
    count_mean, count_std = pct_to_count(pct_mean, pct_std, themes_mean)
    s = f"{count_mean:.1f}±{count_std:.1f}"
    return f"{s:^{width}}"


def print_group_table(
    datasets: dict[str, AggStats],
    name_w: int,
    cw: int,
    headers: tuple[str, str, str, str, str, str],
    fields: tuple[str, str, str, str, str, str],
) -> None:
    """Print one Dataset/runs/themes table with 6 mean±std columns (3 Norm, 3 kNN), where each
    `fields` entry is an AggStats field prefix (combined with `_mean`/`_std` to read its value)."""
    header = (
        f"  {'Dataset':<{name_w}} | runs | themes"
        f" | {headers[0]:^{cw}} | {headers[1]:^{cw}} | {headers[2]:^{cw}}"
        f" | {headers[3]:^{cw}} | {headers[4]:^{cw}} | {headers[5]:^{cw}}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for dataset_name, s in sorted(datasets.items(), key=lambda kv: natural_sort_key(kv[0])):
        themes_str = f"{s.themes_mean:.0f}±{s.themes_std:.0f}"
        cells = " | ".join(
            fmt_count(getattr(s, f"{field}_mean"), getattr(s, f"{field}_std"), s.themes_mean, cw)
            for field in fields
        )
        print(f"  {dataset_name:<{name_w}} | {s.n_runs:^4} | {themes_str:^6} | {cells}")


def print_summary(
    summary: dict[str, dict[str, AggStats]],
    gt1_name: str,
    gt2_name: str,
    gt1_counts_by_question: dict[str, int],
    gt2_counts_by_question: dict[str, int],
) -> None:
    g1 = gt1_name[:10]
    g2 = gt2_name[:10]
    cw = max(len(g1), len(g2), 4) + 9  # wide enough for "mean±std"

    for question, datasets in sorted(summary.items()):
        print(f"\n{question}")
        print(
            f"  Consensus ground truth themes: {gt1_name}={gt1_counts_by_question.get(question, 0)}, "
            f"{gt2_name}={gt2_counts_by_question.get(question, 0)}"
        )
        name_w = max(len(n) for n in datasets)

        print_group_table(
            datasets, name_w, cw,
            headers=("Norm→" + g1, "Norm→both", "Norm→" + g2, "kNN→" + g1, "kNN→both", "kNN→" + g2),
            fields=("norm_gt1", "norm_both", "norm_gt2", "knn_gt1", "knn_both", "knn_gt2"),
        )

        print(f"\n  {question} (inclusive — themes in 'both' counted in each overlapping group)")
        print_group_table(
            datasets, name_w, cw,
            headers=(
                f"Norm→{g1}(+both)", f"Norm→{g2}(+both)", "Norm overlap",
                f"kNN→{g1}(+both)", f"kNN→{g2}(+both)", "kNN overlap",
            ),
            fields=(
                "norm_g1_inc_both", "norm_g2_inc_both", "norm_both",
                "knn_g1_inc_both", "knn_g2_inc_both", "knn_both",
            ),
        )


def plot_summary(
    summary: dict[str, dict[str, AggStats]],
    gt1_name: str,
    gt2_name: str,
    gt1_counts_by_question: dict[str, int],
    gt2_counts_by_question: dict[str, int],
    output_dir: Path,
    dataset_order: list[int] | None,
) -> None:
    """For each question, chart the inclusive kNN theme counts (kNN→GT1(+both), kNN→GT2(+both),
    kNN overlap) per dataset against horizontal reference lines for each GT's consensus size."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for question, datasets in sorted(summary.items()):
        names = sorted(datasets.keys(), key=lambda n: dataset_sort_key(n, dataset_order))

        def series(field: str) -> tuple[list[float], list[float]]:
            means, stds = [], []
            for name in names:
                s = datasets[name]
                mean, std = pct_to_count(getattr(s, f"{field}_mean"), getattr(s, f"{field}_std"), s.themes_mean)
                means.append(mean)
                stds.append(std)
            return means, stds

        g1_means, g1_stds = series("knn_g1_inc_both")
        g2_means, g2_stds = series("knn_g2_inc_both")
        overlap_means, overlap_stds = series("knn_both")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=names, y=g1_means, error_y=dict(type="data", array=g1_stds),
            mode="lines+markers", name=f"kNN→{gt1_name} (+both)",
        ))
        fig.add_trace(go.Scatter(
            x=names, y=g2_means, error_y=dict(type="data", array=g2_stds),
            mode="lines+markers", name=f"kNN→{gt2_name} (+both)",
        ))
        fig.add_trace(go.Scatter(
            x=names, y=overlap_means, error_y=dict(type="data", array=overlap_stds),
            mode="lines+markers", name="kNN overlap",
        ))

        gt1_count = gt1_counts_by_question.get(question, 0)
        gt2_count = gt2_counts_by_question.get(question, 0)
        fig.add_hline(y=gt1_count, line_dash="dash", annotation_text=f"{gt1_name} consensus ({gt1_count})")
        fig.add_hline(y=gt2_count, line_dash="dot", annotation_text=f"{gt2_name} consensus ({gt2_count})")

        fig.update_layout(
            title=f"{question}: kNN theme counts (inclusive) vs consensus ground truth size",
            xaxis_title="Dataset",
            yaxis_title="Theme count",
            xaxis=dict(type="category", categoryorder="array", categoryarray=names),
        )

        out_path = output_dir / f"{question}.html"
        fig.write_html(out_path)
        print(f"  Chart written to {out_path}", file=sys.stderr)


def analyse(
    search_dir: Path,
    gt1_name: str,
    gt2_name: str,
    test_name: str | None,
    k: int = DEFAULT_K,
    norm_both_threshold: float = NORM_BOTH_THRESHOLD,
    dataset_order: list[int] | None = None,
) -> None:
    gt2_by_question = load_themes_by_question(search_dir / gt2_name, "consensus")
    gt1_by_question = load_themes_by_question(search_dir / gt1_name, "consensus")
    questions = sorted(gt1_by_question.keys() & gt2_by_question.keys())

    if not questions:
        print("No questions found in GT consensus directories. Run build_consensus_gt.py first.", file=sys.stderr)
        sys.exit(1)

    if test_name:
        test_root = search_dir / test_name
        dataset_dirs = sorted((d for d in test_root.iterdir() if d.is_dir()), key=lambda d: natural_sort_key(d.name))
    else:
        dataset_dirs = sorted(
            (d for d in search_dir.iterdir() if d.is_dir() and d.name not in (gt1_name, gt2_name)),
            key=lambda d: natural_sort_key(d.name),
        )

    if not dataset_dirs:
        print("No comparison datasets found.")
        return

    log_dir = search_dir / "analysis_logs"
    log_dir.mkdir(exist_ok=True)

    cache_key = test_name or "all"
    cache_path = search_dir / f".embeddings_cache_{cache_key}_{EMBEDDING_MODEL}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    client = make_client()

    # question -> dataset_name -> AggStats
    summary: dict[str, dict[str, AggStats]] = defaultdict(dict)

    gt1_embs_by_q: dict[str, list[np.ndarray]] = {}
    gt2_embs_by_q: dict[str, list[np.ndarray]] = {}
    gt1_stats_by_q: dict[str, tuple[np.ndarray, float]] = {}
    gt2_stats_by_q: dict[str, tuple[np.ndarray, float]] = {}

    try:
        print(f"Loading consensus ground truth embeddings (k={k})...", file=sys.stderr)
        for question in questions:
            gt1_embs = fetch_embeddings(
                [t["topic_description"] for t in gt1_by_question[question]], client, cache
            )
            gt2_embs = fetch_embeddings(
                [t["topic_description"] for t in gt2_by_question[question]], client, cache
            )
            gt1_embs_by_q[question] = gt1_embs
            gt2_embs_by_q[question] = gt2_embs
            gt1_stats_by_q[question] = cluster_stats(gt1_embs)
            gt2_stats_by_q[question] = cluster_stats(gt2_embs)
            print(f"  {question}: {gt1_name}={len(gt1_embs)} themes, {gt2_name}={len(gt2_embs)} themes", file=sys.stderr)

        for dataset_dir in dataset_dirs:
            runs = load_runs(dataset_dir)
            if not runs:
                print(f"  {dataset_dir.name}: no run_* directories found, skipping.", file=sys.stderr)
                continue

            print(f"Analysing {dataset_dir.name} ({len(runs)} run(s))...", file=sys.stderr)

            # {question: [counts_from_run_1, counts_from_run_2, ...]}
            counts_by_question: dict[str, list[tuple[int, int, int, int, int, int]]] = defaultdict(list)

            for run_num, themes_by_question in sorted(runs.items()):
                log_path = log_dir / f"{dataset_dir.name}_run_{run_num}.log"
                results = analyse_dataset(
                    dataset_dir.name, themes_by_question, questions,
                    gt1_name, gt2_name,
                    gt1_embs_by_q, gt2_embs_by_q, gt1_stats_by_q, gt2_stats_by_q,
                    client, cache, log_path, k=k, norm_both_threshold=norm_both_threshold,
                )
                for question, counts in results.items():
                    counts_by_question[question].append(counts)

            for question, all_counts in counts_by_question.items():
                summary[question][dataset_dir.name] = aggregate(all_counts)

    finally:
        cache_path.write_text(json.dumps(cache))
        print(f"Embedding cache saved to {cache_path}", file=sys.stderr)

    gt1_counts_by_question = {q: len(themes) for q, themes in gt1_by_question.items()}
    gt2_counts_by_question = {q: len(themes) for q, themes in gt2_by_question.items()}
    print_summary(summary, gt1_name, gt2_name, gt1_counts_by_question, gt2_counts_by_question)
    plot_summary(
        summary, gt1_name, gt2_name, gt1_counts_by_question, gt2_counts_by_question,
        search_dir / "charts", dataset_order,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare test dataset themes against consensus GTs via normalised distance and k-NN. "
                    "Aggregates results across all run_* subdirectories and reports mean±std proportions."
    )
    parser.add_argument("directory", type=Path, help="Root directory containing GT and dataset subdirectories")
    parser.add_argument("ground_truth_1", help="Name of the first ground truth directory")
    parser.add_argument("ground_truth_2", help="Name of the second ground truth directory")
    parser.add_argument("test_dir", nargs="?", default=None, help="Subdirectory containing comparison datasets (optional; defaults to all non-GT dirs)")
    parser.add_argument("--knn-num-neighbours", type=int, default=DEFAULT_K, help=f"k for k-NN classification (default: {DEFAULT_K})")
    parser.add_argument(
        "--norm-both-threshold", type=float, default=NORM_BOTH_THRESHOLD,
        help="min(d1,d2)/max(d1,d2) ratio above which a theme's normalised-distance classification "
             f"is treated as ambiguous ('both') rather than assigned to one GT group (default: {NORM_BOTH_THRESHOLD})",
    )
    parser.add_argument(
        "--dataset-order", type=lambda s: [int(x) for x in s.split(",")], default=None,
        help="Comma-separated dataset numbers (matched against the first integer in each dataset "
             "directory name) giving the left-to-right order for chart x-axes, e.g. "
             "4,10,8,9,3,5,6,7. Datasets not listed fall back to natural sort order, after any listed.",
    )
    args = parser.parse_args()

    analyse(
        args.directory, args.ground_truth_1, args.ground_truth_2, args.test_dir,
        k=args.knn_num_neighbours, norm_both_threshold=args.norm_both_threshold,
        dataset_order=args.dataset_order,
    )
