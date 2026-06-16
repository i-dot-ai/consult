"""Analyse theme similarity between comparison datasets and two ground truth datasets.

For each question, embeds themes from run_1 (or a specified run) using a text
embedding model, then assigns each comparison theme to whichever ground truth
group it is closest to via cosine similarity.

Expected directory structure:
  <search_dir>/<dataset_name>/outputs/run_<n>/.../question_part_<N>/clustered_themes.json
"""

import argparse
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-large"
CACHE_FILENAME = ".embeddings_cache.json"


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
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


def analyse(search_dir: Path, gt1_name: str, gt2_name: str, run: int) -> None:
    files = sorted(search_dir.glob(f"*/outputs/run_{run}/**/clustered_themes.json"))
    if not files:
        print(f"No clustered_themes.json files found for run_{run} under {search_dir}")
        return

    # question -> dataset_name -> [theme dicts]
    by_question: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for path in files:
        dataset = path.relative_to(search_dir).parts[0]
        question = path.parent.name
        by_question[question][dataset] = load_themes(path)

    client = make_client()
    cache_path = search_dir / CACHE_FILENAME
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    try:
        for question, datasets in sorted(by_question.items()):
            if gt1_name not in datasets or gt2_name not in datasets:
                print(f"\n{question}: ground truth dataset(s) missing, skipping.")
                continue

            comparison = {k: v for k, v in datasets.items() if k not in (gt1_name, gt2_name)}
            if not comparison:
                print(f"\n{question}: no comparison datasets found.")
                continue

            print(f"\n{'='*60}\n{question}\n{'='*60}")

            gt1_embeddings = fetch_embeddings(
                [t["topic_description"] for t in datasets[gt1_name]], client, cache
            )
            gt2_embeddings = fetch_embeddings(
                [t["topic_description"] for t in datasets[gt2_name]], client, cache
            )

            for dataset_name, themes in sorted(comparison.items()):
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
    parser.add_argument("directory", type=Path, help="Directory containing dataset subdirectories")
    parser.add_argument("ground_truth_1", help="Name of the first ground truth dataset")
    parser.add_argument("ground_truth_2", help="Name of the second ground truth dataset")
    parser.add_argument("--run", type=int, default=1, help="Run number to use (default: 1)")
    args = parser.parse_args()

    analyse(args.directory, args.ground_truth_1, args.ground_truth_2, args.run)
