"""Analyse theme similarity between comparison datasets and two ground truth datasets.

For each question, embeds themes using a text embedding model, then assigns each
comparison theme to whichever ground truth group it is closest to via cosine similarity.

Expected directory structure:
  <search_dir>/
    <gt1_name>/.../question_part_<N>/clustered_themes.json
    <gt2_name>/.../question_part_<N>/clustered_themes.json
    <test_name>/<dataset_name>/.../question_part_<N>/clustered_themes.json
"""

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.home() / "Code" / "consult" / ".env")

EMBEDDING_MODEL = "text-embedding-3-large"
CACHE_FILENAME = ".embeddings_cache.json"


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        http_client=httpx.Client(verify=False),
    )


def cosine_similarity(a: list[float], b: list[float]) -> float:
    an, bn = np.array(a), np.array(b)
    denom = np.linalg.norm(an) * np.linalg.norm(bn)
    return float(np.dot(an, bn) / denom) if denom else 0.0


def load_themes(path: Path) -> list[dict]:
    with path.open() as f:
        return json.load(f)["theme_nodes"]


def fetch_embeddings(texts: list[str], client: OpenAI, cache: dict[str, list[float]]) -> list[list[float]]:
    missing = [t for t in texts if t not in cache]
    if missing:
        print(f"  Fetching {len(missing)} embedding(s)...")
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=missing)
        for text, item in zip(missing, response.data):
            cache[text] = item.embedding
    return [cache[t] for t in texts]


def max_similarity(embedding: list[float], group_embeddings: list[list[float]]) -> float:
    return max(cosine_similarity(embedding, g) for g in group_embeddings)


def load_themes_by_question(root: Path, run: int) -> dict[str, list[dict]]:
    """Return {question_name: [themes]} for all clustered_themes.json under root matching run_<n>."""
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

    questions = sorted(gt1_by_question.keys() | gt2_by_question.keys())

    client = make_client()
    cache_path = search_dir / CACHE_FILENAME
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    try:
        for question in questions:
            if question not in gt1_by_question or question not in gt2_by_question:
                print(f"\n{question}: missing from one or both ground truth datasets, skipping.")
                continue

            print(f"\n{'='*60}\n{question}\n{'='*60}")

            gt1_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt1_by_question[question]], client, cache
            )
            gt2_embeddings = fetch_embeddings(
                [t["topic_description"] for t in gt2_by_question[question]], client, cache
            )

            for dataset_name, themes_by_question in sorted(comparison_datasets.items()):
                if question not in themes_by_question:
                    print(f"\n  {dataset_name}: question not found, skipping.")
                    continue

                themes = themes_by_question[question]
                print(f"\n  {dataset_name}")
                theme_texts = [t["topic_description"] for t in themes]
                theme_embeddings = fetch_embeddings(theme_texts, client, cache)

                col_width = max(len(t) for t in theme_texts)
                header = f"    {'Theme':<{col_width}} | Group | Sim({gt1_name[:12]}) | Sim({gt2_name[:12]})"
                print(header)
                print("    " + "-" * (len(header) - 4))

                for theme, emb in zip(themes, theme_embeddings):
                    sim1 = max_similarity(emb, gt1_embeddings)
                    sim2 = max_similarity(emb, gt2_embeddings)
                    group = "1" if sim1 >= sim2 else "2"
                    desc = theme["topic_description"]
                    print(f"    {desc:<{col_width}} |   {group}   | {sim1:.3f}         | {sim2:.3f}")
    finally:
        cache_path.write_text(json.dumps(cache))
        print(f"\nEmbedding cache saved to {cache_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assign comparison themes to ground truth groups via embedding similarity."
    )
    parser.add_argument("directory", type=Path, help="Root directory containing gt and test subdirectories")
    parser.add_argument("ground_truth_1", help="Name of the first ground truth directory")
    parser.add_argument("ground_truth_2", help="Name of the second ground truth directory")
    parser.add_argument("test_dir", help="Name of the directory containing comparison datasets")
    parser.add_argument("--run", type=int, default=1, help="Run number to use (default: 1)")
    args = parser.parse_args()

    analyse(args.directory, args.ground_truth_1, args.ground_truth_2, args.test_dir, args.run)
