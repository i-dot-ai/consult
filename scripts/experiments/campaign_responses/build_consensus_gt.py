"""Build a consensus ground truth from multiple theme-generation runs.

Hybrid approach:
  1. Embed all themes from all runs for each question.
  2. Cluster with agglomerative clustering (cosine distance) to group paraphrases.
  3. Keep clusters where themes came from >= MIN_COVERAGE fraction of total runs.
  4. LLM synthesises a clean representative label+description for each surviving cluster.

Writes to:
  <search_dir>/<gt_name>/consensus/question_part_<N>/clustered_themes.json

Each output theme node includes a `run_coverage` field (e.g. 0.8 = present in 4/5 runs).

Expected input structure:
  <search_dir>/
    <gt_name>/
      run_1/.../question_part_<N>/clustered_themes.json
      run_2/.../question_part_<N>/clustered_themes.json
      ...
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from sklearn.cluster import AgglomerativeClustering

load_dotenv(Path.home() / "Code" / "consult" / ".env")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-large-sweden"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_DISTANCE_THRESHOLD = 0.15  # cosine distance ≈ 0.85 similarity
DEFAULT_MIN_COVERAGE = 0.5         # theme must appear in >= this fraction of runs
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0


class ClusterRepresentative(BaseModel):
    topic_label: str = Field(description="Short theme name (2-5 words)")
    topic_description: str = Field(description="Concise description (15-25 words max)")


class SynthesisResponse(BaseModel):
    clusters: list[ClusterRepresentative]


SYNTHESIS_SYSTEM_PROMPT = """You are an expert at synthesising similar theme descriptions into a single clear representative.

For each cluster of similar themes, write ONE representative label and description that best captures what the cluster is about.

## Output format
- topic_label: 2-5 words (e.g. "Fiscal cost concerns")
- topic_description: ONE concise sentence, 15-25 words max, describing what responses in this theme argue

Return one entry per cluster, in the same order as the input."""


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        http_client=httpx.Client(verify=False),
    )


def load_themes(path: Path) -> list[dict]:
    with path.open() as f:
        return json.load(f)["theme_nodes"]


def load_all_runs(gt_root: Path) -> dict[str, list[tuple[dict, int]]]:
    """Return {question: [(theme_dict, run_num), ...]} across all run_* dirs."""
    by_question: dict[str, list[tuple[dict, int]]] = {}
    run_dirs = sorted(d for d in gt_root.iterdir() if d.is_dir() and d.name.startswith("run_"))
    if not run_dirs:
        logger.error(f"No run_* directories found in {gt_root}")
        sys.exit(1)

    for run_dir in run_dirs:
        try:
            run_num = int(run_dir.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        for path in sorted(run_dir.rglob("clustered_themes.json")):
            question = path.parent.name
            for theme in load_themes(path):
                by_question.setdefault(question, []).append((theme, run_num))
        logger.info(f"  Loaded {run_dir.name}")

    return by_question


def fetch_embeddings(texts: list[str], client: OpenAI, cache: dict[str, list[float]]) -> np.ndarray:
    missing = [t for t in texts if t not in cache]
    if missing:
        logger.info(f"  Fetching {len(missing)} embedding(s)...")
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=missing)
        for text, item in zip(missing, response.data):
            cache[text] = item.embedding
    return np.array([cache[t] for t in texts])


def cluster_themes(
    themes_with_runs: list[tuple[dict, int]],
    embeddings: np.ndarray,
    total_runs: int,
    distance_threshold: float,
    min_coverage: float,
) -> list[tuple[list[tuple[dict, int]], float]]:
    """Cluster themes, return surviving (members, coverage) pairs above min_coverage."""
    if len(themes_with_runs) == 1:
        return [(themes_with_runs, 1.0)]

    # Normalise for cosine distance
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.where(norms > 0, norms, 1)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=distance_threshold,
    )
    labels = clustering.fit_predict(normed)

    clusters: dict[int, list[tuple[dict, int]]] = {}
    for (theme, run_num), label in zip(themes_with_runs, labels):
        clusters.setdefault(int(label), []).append((theme, run_num))

    surviving = []
    for members in clusters.values():
        distinct_runs = len({run_num for _, run_num in members})
        coverage = distinct_runs / total_runs
        if coverage >= min_coverage:
            surviving.append((members, coverage))

    return sorted(surviving, key=lambda x: -x[1])


def synthesise_labels(
    clusters: list[tuple[list[tuple[dict, int]], float]],
    question: str,
    client: OpenAI,
    model: str,
) -> list[ClusterRepresentative]:
    """One LLM call to produce a representative label+description for each cluster."""
    cluster_blocks = []
    for i, (members, coverage) in enumerate(clusters, 1):
        runs_str = f"{len({r for _, r in members})}/{len(members)} unique run(s)"
        theme_lines = "\n".join(
            f"  - {t['topic_label']}: {t['topic_description']}" for t, _ in members
        )
        cluster_blocks.append(f"## Cluster {i} ({runs_str})\n{theme_lines}")

    human_prompt = f"""Question: {question}

{chr(10).join(cluster_blocks)}

Write one representative label and description for each of the {len(clusters)} clusters above, in order."""

    messages = [
        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            result = (
                client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=SynthesisResponse,
                )
                .choices[0]
                .message.parsed
            )
            if len(result.clusters) != len(clusters):
                raise ValueError(
                    f"Expected {len(clusters)} cluster representatives, got {len(result.clusters)}"
                )
            return result.clusters
        except Exception as e:
            last_error = e
            if isinstance(e, (ValidationError, ValueError)) and attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_DELAY_SECONDS * (2 ** attempt))
                continue
            raise

    raise last_error  # type: ignore[misc]


def _generate_topic_ids(n: int) -> list[str]:
    ids = []
    for i in range(n):
        if i < 26:
            ids.append(chr(65 + i))
        else:
            ids.append(chr(65 + ((i - 26) // 26)) + chr(65 + ((i - 26) % 26)))
    return ids


def build_consensus_for_question(
    question: str,
    themes_with_runs: list[tuple[dict, int]],
    client: OpenAI,
    cache: dict[str, list[float]],
    model: str,
    distance_threshold: float,
    min_coverage: float,
) -> list[dict]:
    all_runs = {run_num for _, run_num in themes_with_runs}
    total_runs = len(all_runs)

    texts = [t["topic_description"] for t, _ in themes_with_runs]
    embeddings = fetch_embeddings(texts, client, cache)

    clusters = cluster_themes(themes_with_runs, embeddings, total_runs, distance_threshold, min_coverage)

    dropped = len(themes_with_runs) - sum(len(m) for m, _ in clusters)
    kept = sum(len(m) for m, _ in clusters)
    logger.info(
        f"  {question}: {len(themes_with_runs)} themes → "
        f"{len(clusters)} clusters surviving (coverage>={min_coverage:.0%}), "
        f"including {kept} themes kept, {dropped} dropped as higher than threshold"
    )

    representatives = synthesise_labels(clusters, question, client, model)

    topic_ids = _generate_topic_ids(len(clusters))
    return [
        {
            "topic_id": topic_ids[i],
            "topic_label": rep.topic_label,
            "topic_description": rep.topic_description,
            "run_coverage": round(coverage, 3),
        }
        for i, (rep, (_, coverage)) in enumerate(zip(representatives, clusters))
    ]


def write_consensus(gt_root: Path, question: str, themes: list[dict]) -> Path:
    out_dir = gt_root / "consensus" / question
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "clustered_themes.json"
    out_path.write_text(json.dumps({"theme_nodes": themes}, indent=2))
    return out_path


def build(
    gt_dir: Path,
    model: str,
    distance_threshold: float,
    min_coverage: float,
) -> None:
    if not gt_dir.is_dir():
        logger.error(f"Directory not found: {gt_dir}")
        sys.exit(1)

    client = make_client()
    cache_path = gt_dir / f".embeddings_cache_consensus_{EMBEDDING_MODEL}.json"
    cache: dict[str, list[float]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    try:
        by_question = load_all_runs(gt_dir)
        for question, themes_with_runs in sorted(by_question.items()):
            themes = build_consensus_for_question(
                question, themes_with_runs, client, cache, model,
                distance_threshold, min_coverage,
            )
            out_path = write_consensus(gt_dir, question, themes)
            logger.info(f"  {len(themes)} consensus themes → {out_path}")
    finally:
        cache_path.write_text(json.dumps(cache))
        logger.info(f"\nEmbedding cache saved to {cache_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build consensus GT from multiple runs via clustering + LLM synthesis."
    )
    parser.add_argument("gt_dir", type=Path, help="Path to the GT directory containing run_* subdirectories")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"LLM model for label synthesis (default: {DEFAULT_MODEL})")
    parser.add_argument("--distance-threshold", type=float, default=DEFAULT_DISTANCE_THRESHOLD,
                        help=f"Cosine distance threshold for clustering (default: {DEFAULT_DISTANCE_THRESHOLD}; lower = stricter)")
    parser.add_argument("--min-coverage", type=float, default=DEFAULT_MIN_COVERAGE,
                        help=f"Min fraction of runs a cluster must span to survive (default: {DEFAULT_MIN_COVERAGE})")
    args = parser.parse_args()

    build(args.gt_dir, args.model, args.distance_threshold, args.min_coverage)
