"""Analyse theme similarity between comparison datasets and two ground truth datasets.

For each question:
  1. Embeds all themes via a text embedding model.
  2. Computes a centroid and mean distance from centroid for each GT group.
  3. For each test theme, computes a normalised distance to each GT cluster and
     performs k-NN (k=3) across both groups.
  4. Writes detailed per-dataset output to log files; prints a summary table to stdout.

Expected directory structure:
  <search_dir>/
    <gt1_name>/.../question_part_<N>/clustered_themes.json
    <gt2_name>/.../question_part_<N>/clustered_themes.json
    [<test_name>/]<dataset_name>/.../question_part_<N>/clustered_themes.json

If test_dir is omitted, all directories in search_dir other than the two GT dirs are analysed.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from io import StringIO
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.home() / "Code" / "consult" / ".env")

EMBEDDING_MODEL = "text-embedding-3-large"
K = 3


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        http_client=httpx.Client(verify=False),
    )


def load_themes(path: Path) -> list[dict]:
    with path.open() as f:
        return json.load(f)["theme_nodes"]


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


def knn_group(embedding: np.ndarray, gt1_embeddings: list[np.ndarray], gt2_embeddings: list[np.ndarray]) -> tuple[str, int, int]:
    neighbours = (
        [(float(np.linalg.norm(embedding - e)), "1") for e in gt1_embeddings]
        + [(float(np.linalg.norm(embedding - e)), "2") for e in gt2_embeddings]
    )
    top_k = sorted(neighbours, key=lambda x: x[0])[:K]
    gt1_votes = sum(1 for _, g in top_k if g == "1")
    gt2_votes = K - gt1_votes
    return ("1" if gt1_votes >= gt2_votes else "2"), gt1_votes, gt2_votes


def load_themes_by_question(root: Path, run: int) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for path in sorted(root.rglob("clustered_themes.json")):
        if f"run_{run}" not in path.parts:
            continue
        result[path.parent.name] = load_themes(path)
    return result


def analyse_dataset(
    dataset_name: str,
    themes_by_question: dict[str, list[dict]],
    questions: list[str],
    gt1_name: str,
    gt2_name: str,
    gt1_by_question: dict[str, list[dict]],
    gt2_by_question: dict[str, list[dict]],
    client: OpenAI,
    cache: dict[str, list[float]],
    log_path: Path,
) -> dict[str, tuple[int, int, int, int]]:
    """Run analysis for one dataset. Writes detail to log_path.
    Returns {question: (norm_gt1, norm_gt2, knn_gt1, knn_gt2)}."""

    results: dict[str, tuple[int, int, int, int]] = {}

    with log_path.open("w") as log:
        def out(line: str = "") -> None:
            log.write(line + "\n")

        out(f"Analysis: {dataset_name}")
        out("=" * 60)

        for question in questions:
            if question not in themes_by_question:
                out(f"\n{question}: not found in this dataset, skipping.")
                continue

            gt1_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt1_by_question[question]], client, cache
            )
            gt2_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt2_by_question[question]], client, cache
            )
            gt1_centroid, gt1_mean = cluster_stats(gt1_embeddings)
            gt2_centroid, gt2_mean = cluster_stats(gt2_embeddings)

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
            header = f"  Theme | Norm Grp | {g1_label} | {g2_label} | kNN Grp | Votes"
            out(f"\n{header}")
            out("  " + "-" * (len(header) - 2))

            norm_gt1 = norm_gt2 = knn_gt1 = knn_gt2 = 0
            for label, theme, emb in zip(labels, themes, theme_embeddings):
                d1 = normalised_distance(emb, gt1_centroid, gt1_mean)
                d2 = normalised_distance(emb, gt2_centroid, gt2_mean)
                norm_group = "1" if d1 <= d2 else "2"
                knn_winner, v1, v2 = knn_group(emb, gt1_embeddings, gt2_embeddings)
                out(f"  {label:<5} |    {norm_group}    | {d1:.3f}      | {d2:.3f}      |    {knn_winner}    | {v1}-{v2}")
                if norm_group == "1": norm_gt1 += 1
                else: norm_gt2 += 1
                if knn_winner == "1": knn_gt1 += 1
                else: knn_gt2 += 1

            out()
            for label, text in zip(labels, theme_texts):
                out(f"  {label}: {text}")

            results[question] = (norm_gt1, norm_gt2, knn_gt1, knn_gt2)

    return results


def print_summary(
    summary: dict[str, dict[str, tuple[int, int, int, int]]],
    gt1_name: str,
    gt2_name: str,
) -> None:
    for question, datasets in sorted(summary.items()):
        print(f"\n{question}")
        name_w = max(len(n) for n in datasets)
        g1 = gt1_name[:10]
        g2 = gt2_name[:10]
        header = f"  {'Dataset':<{name_w}} | Norm→{g1} | Norm→{g2} | kNN→{g1} | kNN→{g2}"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for dataset_name, (n1, n2, k1, k2) in sorted(datasets.items()):
            print(f"  {dataset_name:<{name_w}} | {n1:^{5+len(g1)}} | {n2:^{5+len(g2)}} | {k1:^{4+len(g1)}} | {k2:^{4+len(g2)}}")


def analyse(
    search_dir: Path,
    gt1_name: str,
    gt2_name: str,
    test_name: str | None,
    run: int,
) -> None:
    gt1_by_question = load_themes_by_question(search_dir / gt1_name, run)
    gt2_by_question = load_themes_by_question(search_dir / gt2_name, run)
    questions = sorted(gt1_by_question.keys() & gt2_by_question.keys())

    if test_name:
        test_root = search_dir / test_name
        dataset_dirs = sorted(d for d in test_root.iterdir() if d.is_dir())
    else:
        dataset_dirs = sorted(
            d for d in search_dir.iterdir()
            if d.is_dir() and d.name not in (gt1_name, gt2_name)
        )

    if not dataset_dirs:
        print("No comparison datasets found.")
        return

    log_dir = search_dir / "analysis_logs"
    log_dir.mkdir(exist_ok=True)

    cache_key = test_name or "all"
    cache_path = search_dir / f".embeddings_cache_{cache_key}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    client = make_client()

    # question -> dataset_name -> (norm_gt1, norm_gt2, knn_gt1, knn_gt2)
    summary: dict[str, dict[str, tuple[int, int, int, int]]] = defaultdict(dict)

    try:
        for dataset_dir in dataset_dirs:
            themes_by_question = load_themes_by_question(dataset_dir, run)
            log_path = log_dir / f"{dataset_dir.name}.log"
            print(f"Analysing {dataset_dir.name} → {log_path}", file=sys.stderr)

            results = analyse_dataset(
                dataset_dir.name, themes_by_question, questions,
                gt1_name, gt2_name, gt1_by_question, gt2_by_question,
                client, cache, log_path,
            )
            for question, counts in results.items():
                summary[question][dataset_dir.name] = counts
    finally:
        cache_path.write_text(json.dumps(cache))
        print(f"Embedding cache saved to {cache_path}", file=sys.stderr)

    print_summary(summary, gt1_name, gt2_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assign comparison themes to GT groups via normalised distance and k-NN."
    )
    parser.add_argument("directory", type=Path, help="Root directory containing gt and dataset subdirectories")
    parser.add_argument("ground_truth_1", help="Name of the first ground truth directory")
    parser.add_argument("ground_truth_2", help="Name of the second ground truth directory")
    parser.add_argument("test_dir", nargs="?", default=None, help="Directory containing comparison datasets (optional)")
    parser.add_argument("--run", type=int, default=1, help="Run number to use (default: 1)")
    args = parser.parse_args()

    analyse(args.directory, args.ground_truth_1, args.ground_truth_2, args.test_dir, args.run)
