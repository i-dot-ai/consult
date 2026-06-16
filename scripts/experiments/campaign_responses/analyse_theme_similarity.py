"""Analyse theme similarity between comparison datasets and two ground truth datasets.

For each question:
  1. Embeds all themes via a text embedding model.
  2. Computes a centroid and the stddev of distances-from-centroid for each GT group.
  3. For each test theme, computes a normalised distance (z-score of distance from
     centroid relative to the group's own spread) to each GT cluster — a scalar
     approximation of Mahalanobis distance suitable for high-dimensional, small-sample data.
  4. Assigns the theme to the closer cluster (lower normalised distance).

Expected directory structure:
  <search_dir>/
    <gt1_name>/.../question_part_<N>/clustered_themes.json
    <gt2_name>/.../question_part_<N>/clustered_themes.json
    <test_name>/<dataset_name>/.../question_part_<N>/clustered_themes.json
"""

import argparse
import json
import os
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.home() / "Code" / "consult" / ".env")

EMBEDDING_MODEL = "text-embedding-3-large"

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
        print(f"  Fetching {len(missing)} embedding(s)...")
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=missing)
        for text, item in zip(missing, response.data):
            cache[text] = item.embedding
    return [np.array(cache[t]) for t in texts]


def cluster_stats(embeddings: list[np.ndarray]) -> tuple[np.ndarray, float]:
    """Return (centroid, stddev of distances from centroid) for a group of embeddings."""
    centroid = np.mean(embeddings, axis=0)
    dists = [float(np.linalg.norm(e - centroid)) for e in embeddings]
    return centroid, float(np.std(dists, ddof=1))


def mahalanobis_distance(embedding: np.ndarray, centroid: np.ndarray, std_dist: float) -> float:
    """Distance from centroid normalised by the group's own spread."""
    dist = float(np.linalg.norm(embedding - centroid))
    return dist / std_dist if std_dist > 0 else dist


def load_themes_by_question(root: Path, run: int) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for path in sorted(root.rglob("clustered_themes.json")):
        if f"run_{run}" not in path.parts:
            continue
        result[path.parent.name] = load_themes(path)
    return result


def analyse(search_dir: Path, gt1_name: str, gt2_name: str, test_name: str, run: int) -> None:
    gt1_by_question = load_themes_by_question(search_dir / gt1_name, run)
    gt2_by_question = load_themes_by_question(search_dir / gt2_name, run)

    test_dir = search_dir / test_name
    comparison_datasets = {
        d.name: load_themes_by_question(d, run)
        for d in sorted(test_dir.iterdir())
        if d.is_dir()
    }

    if not comparison_datasets:
        print(f"No comparison datasets found under {test_dir}")
        return

    questions = sorted(gt1_by_question.keys() & gt2_by_question.keys())

    client = make_client()
    cache_path = search_dir / f".embeddings_cache_{test_name}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    try:
        for question in questions:
            print(f"\n{'='*60}\n{question}\n{'='*60}")

            gt1_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt1_by_question[question]], client, cache
            )
            gt2_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt2_by_question[question]], client, cache
            )

            gt1_centroid, gt1_std = cluster_stats(gt1_embeddings)
            gt2_centroid, gt2_std = cluster_stats(gt2_embeddings)

            print(f"\n  GT cluster stats:")
            print(f"    {gt1_name}: stddev of distances from centroid={gt1_std:.4f} ({len(gt1_embeddings)} themes)")
            print(f"    {gt2_name}: stddev of distances from centroid={gt2_std:.4f} ({len(gt2_embeddings)} themes)")

            for dataset_name, themes_by_question in sorted(comparison_datasets.items()):
                if question not in themes_by_question:
                    print(f"\n  {dataset_name}: question not found, skipping.")
                    continue

                themes = themes_by_question[question]
                print(f"\n  {dataset_name}")
                theme_texts = [t["topic_description"] for t in themes]
                theme_embeddings = fetch_embeddings(theme_texts, client, cache)

                col_width = max(len(t) for t in theme_texts)
                g1_label = f"MahDist({gt1_name[:10]})"
                g2_label = f"MahDist({gt2_name[:10]})"
                header = f"    {'Theme':<{col_width}} | Group | {g1_label} | {g2_label}"
                print(header)
                print("    " + "-" * (len(header) - 4))

                for theme, emb in zip(themes, theme_embeddings):
                    d1 = mahalanobis_distance(emb, gt1_centroid, gt1_std)
                    d2 = mahalanobis_distance(emb, gt2_centroid, gt2_std)
                    group = "1" if d1 <= d2 else "2"
                    desc = theme["topic_description"]
                    print(f"    {desc:<{col_width}} |   {group}   | {d1:.3f}        | {d2:.3f}")
    finally:
        cache_path.write_text(json.dumps(cache))
        print(f"\nEmbedding cache saved to {cache_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assign comparison themes to GT groups via Mahalanobis-approximated cluster distance."
    )
    parser.add_argument("directory", type=Path, help="Root directory containing gt and test subdirectories")
    parser.add_argument("ground_truth_1", help="Name of the first ground truth directory")
    parser.add_argument("ground_truth_2", help="Name of the second ground truth directory")
    parser.add_argument("test_dir", help="Name of the directory containing comparison datasets")
    parser.add_argument("--run", type=int, default=1, help="Run number to use (default: 1)")
    args = parser.parse_args()

    analyse(args.directory, args.ground_truth_1, args.ground_truth_2, args.test_dir, args.run)
