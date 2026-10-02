"""Concept-based theme finding.

Why: grouping in embedding space (rather than asking an LLM to merge theme labels)
keeps every theme traceable to the concepts and responses behind it, and uses the
LLM only where judgement is needed: chunking, reviewing clusters, and wording themes.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from themefinder.llm import LLM, Embedder
from themefinder.llm_batch_processor import batch_and_run
from themefinder.models import (
    ClusterList,
    ClusterReview,
    ClusterThemeResponses,
    ConceptExtractionResponses,
)
from themefinder.prompts import (
    CLUSTER_REVIEW,
    CLUSTER_THEME_REFINEMENT,
    CONCEPT_EXTRACTION,
    CONSULTATION_SYSTEM_PROMPT,
)
from themefinder.tasks import assign_sequential_topic_ids
from themefinder.themefinder_logging import logger

NEAR_DUPLICATE_SIMILARITY = 0.9

THEME_COLUMNS = ["topic_id", "topic", "source_topic_count", "position", "cluster_id"]


@dataclass(frozen=True)
class ConceptClusteringConfig:
    """Tunable settings, grouped so the step functions share one set of defaults.

    Sizes are counted in distinct source responses, not concepts, so one verbose
    respondent cannot make a cluster look well supported.
    """

    distance_threshold: float = 0.45
    min_cluster_size: int = 3
    leftover_target_fraction: float = 0.05
    max_review_rounds: int = 5
    min_progress: int = 1
    max_candidates: int = 30
    candidate_distance_factor: float = 1.5
    max_concepts_in_prompt: int = 40
    extraction_batch_size: int = 20
    review_batch_size: int = 5
    refinement_batch_size: int = 10


async def find_themes_via_concepts(
    responses_df: pd.DataFrame,
    llm: LLM,
    embedder: Embedder,
    question: str,
    system_prompt: str = CONSULTATION_SYSTEM_PROMPT,
    concurrency: int = 10,
    config: ConceptClusteringConfig | None = None,
) -> dict[str, str | pd.DataFrame]:
    """Find themes by chunking responses into concepts and clustering them.

    Args:
        responses_df: DataFrame with `response_id` and `response` columns.
        llm: LLM instance for extraction, cluster review and theme writing.
        embedder: Embedder used to cluster concepts.
        question: The survey question.
        system_prompt: System prompt to guide the LLM's behaviour.
        concurrency: Number of concurrent API calls to make.
        config: Clustering and review settings.

    Returns:
        Dictionary with the question, final `themes`, every `concepts` row with its
        cluster, the `outliers` left unallocated (for review), and unprocessable inputs.
    """
    config = config or ConceptClusteringConfig()

    concepts_df, unprocessable_responses = await extract_concepts(
        responses_df,
        llm,
        question,
        system_prompt=system_prompt,
        config=config,
        concurrency=concurrency,
    )
    if concepts_df.empty:
        logger.warning("No concepts extracted, returning no themes")
        return _result(
            question,
            pd.DataFrame(columns=THEME_COLUMNS),
            concepts_df,
            concepts_df,
            unprocessable_responses,
            pd.DataFrame(),
        )

    clustered_df = await embed_and_cluster_concepts(concepts_df, embedder, config)
    reviewed_df = await review_clusters(
        clustered_df,
        llm,
        question,
        system_prompt=system_prompt,
        config=config,
        concurrency=concurrency,
    )
    themes_df, unprocessable_clusters = await refine_cluster_themes(
        reviewed_df,
        llm,
        question,
        system_prompt=system_prompt,
        config=config,
        concurrency=concurrency,
    )
    await _log_near_duplicate_themes(themes_df, embedder)

    logger.info(f"Finished finding themes: {len(themes_df)} themes")
    return _result(
        question,
        themes_df,
        reviewed_df.drop(columns=["embedding"]),
        get_outliers(reviewed_df),
        unprocessable_responses,
        unprocessable_clusters,
    )


def _result(
    question: str,
    themes: pd.DataFrame,
    concepts: pd.DataFrame,
    outliers: pd.DataFrame,
    unprocessables: pd.DataFrame,
    unprocessable_clusters: pd.DataFrame,
) -> dict[str, str | pd.DataFrame]:
    return {
        "question": question,
        "themes": themes,
        "concepts": concepts,
        "outliers": outliers,
        "unprocessables": unprocessables,
        "unprocessable_clusters": unprocessable_clusters,
    }


async def extract_concepts(
    responses_df: pd.DataFrame,
    llm: LLM,
    question: str,
    system_prompt: str = CONSULTATION_SYSTEM_PROMPT,
    config: ConceptClusteringConfig | None = None,
    concurrency: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Break each response into self-contained concepts (step a).

    Returns:
        (concepts with concept_id, source_response_id, text, position; unprocessable responses)
    """
    config = config or ConceptClusteringConfig()
    logger.info(f"Extracting concepts from {len(responses_df)} responses")

    results, unprocessable = await batch_and_run(
        responses_df[["response_id", "response"]].copy(),
        CONCEPT_EXTRACTION,
        llm,
        output_model=ConceptExtractionResponses,
        batch_size=config.extraction_batch_size,
        integrity_check=True,
        question=question,
        system_prompt=system_prompt,
        concurrency=concurrency,
    )

    rows = []
    for _, row in results.iterrows():
        for concept in row["concepts"]:
            text = concept["text"].strip()
            if text:
                rows.append(
                    {
                        "source_response_id": int(row["response_id"]),
                        "text": text,
                        "position": getattr(
                            concept["position"], "value", concept["position"]
                        ),
                    }
                )
    concepts_df = pd.DataFrame(rows, columns=["source_response_id", "text", "position"])
    concepts_df.insert(0, "concept_id", range(1, len(concepts_df) + 1))
    logger.info(f"Extracted {len(concepts_df)} concepts")
    return concepts_df, unprocessable


async def embed_and_cluster_concepts(
    concepts_df: pd.DataFrame,
    embedder: Embedder,
    config: ConceptClusteringConfig | None = None,
) -> pd.DataFrame:
    """Embed concepts and cluster them; small clusters become the leftover pool (step b).

    Adds `embedding`, `cluster_id` (null while a concept is in the leftover pool),
    `rejected_from` and `history` columns.
    """
    config = config or ConceptClusteringConfig()
    df = concepts_df.copy().reset_index(drop=True)

    embeddings = _normalise(await embedder.aembed(df["text"].tolist()))
    df["embedding"] = list(embeddings)
    df["cluster_id"] = pd.array([pd.NA] * len(df), dtype="Int64")
    df["rejected_from"] = [[] for _ in range(len(df))]
    df["history"] = [[] for _ in range(len(df))]

    _cluster_pool(df, config, note="initial clustering")
    logger.info(
        f"Initial clustering: {df['cluster_id'].nunique()} clusters, "
        f"{int(df['cluster_id'].isna().sum())} of {len(df)} concepts in leftover pool"
    )
    return df


async def review_clusters(
    concepts_df: pd.DataFrame,
    llm: LLM,
    question: str,
    system_prompt: str = CONSULTATION_SYSTEM_PROMPT,
    config: ConceptClusteringConfig | None = None,
    concurrency: int = 10,
) -> pd.DataFrame:
    """Let the LLM eject misplaced concepts and pull in leftovers until the pool drains (step c).

    Clusters only exchange concepts with the leftover pool, which keeps each call small.
    Whatever is still in the pool after a final clustering pass stays as outliers.
    """
    config = config or ConceptClusteringConfig()
    df = concepts_df.copy()
    df["rejected_from"] = df["rejected_from"].apply(list)
    df["history"] = df["history"].apply(list)
    total = len(df)

    for round_number in range(1, config.max_review_rounds + 1):
        if df["cluster_id"].notna().sum() == 0:
            break
        removed, added = await _review_round(
            df, llm, question, system_prompt, config, concurrency, round_number
        )
        pool_size = int(df["cluster_id"].isna().sum())
        logger.info(
            f"Review round {round_number}: removed {removed}, added {added}, "
            f"{pool_size} of {total} concepts in leftover pool"
        )
        if pool_size <= config.leftover_target_fraction * total:
            break
        if removed + added < config.min_progress:
            break

    allocated = _cluster_pool(df, config, note="final leftover clustering")
    logger.info(
        f"Final leftover clustering allocated {allocated} concepts; "
        f"{int(df['cluster_id'].isna().sum())} of {total} remain as outliers"
    )
    return df


async def refine_cluster_themes(
    concepts_df: pd.DataFrame,
    llm: LLM,
    question: str,
    system_prompt: str = CONSULTATION_SYSTEM_PROMPT,
    config: ConceptClusteringConfig | None = None,
    concurrency: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write one label and one-sentence description per cluster (step d).

    Returns:
        (themes with topic_id, topic, source_topic_count, position, cluster_id;
        clusters the LLM could not write a theme for)
    """
    config = config or ConceptClusteringConfig()
    clustered = concepts_df[concepts_df["cluster_id"].notna()]
    if clustered.empty:
        return pd.DataFrame(columns=THEME_COLUMNS), pd.DataFrame()

    centroids = _centroids(concepts_df)
    rows = []
    for cluster_id, members in clustered.groupby("cluster_id"):
        shown = _select_members(
            members,
            centroids[int(cluster_id)],
            config.max_concepts_in_prompt,
            include_farthest=False,
        )
        rows.append(
            {
                "response_id": int(cluster_id),
                "total_concepts": len(members),
                "concepts": [
                    {"text": r.text, "position": r.position} for r in shown.itertuples()
                ],
            }
        )
    logger.info(f"Writing themes for {len(rows)} clusters")

    results, unprocessable = await batch_and_run(
        pd.DataFrame(rows),
        CLUSTER_THEME_REFINEMENT,
        llm,
        output_model=ClusterThemeResponses,
        batch_size=config.refinement_batch_size,
        integrity_check=True,
        question=question,
        system_prompt=system_prompt,
        concurrency=concurrency,
    )
    if results.empty:
        return pd.DataFrame(columns=THEME_COLUMNS), unprocessable

    stats = clustered.groupby("cluster_id").agg(
        source_topic_count=("source_response_id", "nunique"),
        position=("position", lambda s: s.mode().iat[0]),
    )
    stats.index = stats.index.astype(int)
    themes = (
        results[["response_id", "topic"]]
        .rename(columns={"response_id": "cluster_id"})
        .merge(stats, left_on="cluster_id", right_index=True)
        .sort_values("source_topic_count", ascending=False)
        .reset_index(drop=True)
    )
    themes = assign_sequential_topic_ids(themes)
    return themes[THEME_COLUMNS], unprocessable


def get_outliers(concepts_df: pd.DataFrame) -> pd.DataFrame:
    """List concepts left out of every cluster, with the nearest cluster to aid review."""
    pool = concepts_df[concepts_df["cluster_id"].isna()]
    centroids = _centroids(concepts_df)

    rows = []
    for row in pool.itertuples():
        nearest_id, nearest_distance = None, None
        if centroids:
            distances = {
                cid: 1 - float(np.dot(row.embedding, centroid))
                for cid, centroid in centroids.items()
            }
            nearest_id = min(distances, key=distances.get)
            nearest_distance = distances[nearest_id]
        rows.append(
            {
                "concept_id": row.concept_id,
                "source_response_id": row.source_response_id,
                "text": row.text,
                "position": row.position,
                "nearest_cluster_id": nearest_id,
                "nearest_cluster_distance": nearest_distance,
                "rejected_from": list(row.rejected_from),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "concept_id",
            "source_response_id",
            "text",
            "position",
            "nearest_cluster_id",
            "nearest_cluster_distance",
            "rejected_from",
        ],
    )


def _normalise(matrix: np.ndarray) -> np.ndarray:
    """Unit-length rows so a dot product is cosine similarity."""
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


def _agglomerative_labels(
    embeddings: np.ndarray, distance_threshold: float
) -> np.ndarray:
    """Cut an average-linkage tree at a distance, so no cluster count is needed."""
    try:
        from sklearn.cluster import AgglomerativeClustering
    except ImportError as e:
        raise ImportError(
            "Concept clustering needs scikit-learn: pip install 'themefinder[concepts]'"
        ) from e
    if len(embeddings) < 2:
        return np.zeros(len(embeddings), dtype=int)
    return AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=distance_threshold,
    ).fit_predict(embeddings)


def _cluster_pool(df: pd.DataFrame, config: ConceptClusteringConfig, note: str) -> int:
    """Cluster the leftover pool in place; groups big enough become new clusters.

    Returns the number of concepts allocated.
    """
    pool_index = df.index[df["cluster_id"].isna()]
    if len(pool_index) < 2:
        return 0

    labels = _agglomerative_labels(
        np.vstack(df.loc[pool_index, "embedding"]), config.distance_threshold
    )
    existing = df["cluster_id"].dropna()
    next_id = int(existing.max()) + 1 if len(existing) else 1

    allocated = 0
    for label in np.unique(labels):
        members = pool_index[labels == label]
        if df.loc[members, "source_response_id"].nunique() < config.min_cluster_size:
            continue
        df.loc[members, "cluster_id"] = next_id
        for index in members:
            df.at[index, "history"].append(f"{note}: cluster {next_id}")
        next_id += 1
        allocated += len(members)
    return allocated


def _centroids(df: pd.DataFrame) -> dict[int, np.ndarray]:
    """Unit-length mean embedding per cluster."""
    centroids = {}
    for cluster_id, members in df[df["cluster_id"].notna()].groupby("cluster_id"):
        mean = np.vstack(members["embedding"]).mean(axis=0, keepdims=True)
        centroids[int(cluster_id)] = _normalise(mean)[0]
    return centroids


def _select_members(
    members: pd.DataFrame,
    centroid: np.ndarray,
    limit: int,
    include_farthest: bool,
) -> pd.DataFrame:
    """Keep prompts bounded: the most central members, plus the likeliest misfits for review."""
    if len(members) <= limit:
        return members
    distances = 1 - np.vstack(members["embedding"]) @ centroid
    order = np.argsort(distances)
    if include_farthest:
        far = limit // 2
        picks = np.concatenate([order[: limit - far], order[-far:]])
    else:
        picks = order[:limit]
    return members.iloc[picks]


def _concept_records(concepts: pd.DataFrame) -> list[dict]:
    return [
        {"concept_id": int(r.concept_id), "text": r.text, "position": r.position}
        for r in concepts.itertuples()
    ]


def _build_review_rows(
    df: pd.DataFrame, centroids: dict[int, np.ndarray], config: ConceptClusteringConfig
) -> list[dict]:
    """One row per cluster: members to check plus nearby pool concepts it could absorb."""
    pool = df[df["cluster_id"].isna()]
    pool_embeddings = np.vstack(pool["embedding"]) if len(pool) else None
    distance_limit = config.distance_threshold * config.candidate_distance_factor

    rows = []
    for cluster_id, centroid in centroids.items():
        members = df[df["cluster_id"] == cluster_id]
        shown = _select_members(
            members, centroid, config.max_concepts_in_prompt, include_farthest=True
        )

        candidates = pool.iloc[0:0]
        if pool_embeddings is not None:
            distances = 1 - pool_embeddings @ centroid
            allowed = np.array(
                [cluster_id not in rejected for rejected in pool["rejected_from"]]
            )
            eligible = np.where(allowed & (distances <= distance_limit))[0]
            nearest = eligible[np.argsort(distances[eligible])][: config.max_candidates]
            candidates = pool.iloc[nearest]

        rows.append(
            {
                "response_id": cluster_id,
                "members": _concept_records(shown),
                "candidates": _concept_records(candidates),
            }
        )
    return rows


async def _run_cluster_reviews(
    rows: list[dict],
    llm: LLM,
    question: str,
    system_prompt: str,
    batch_size: int,
    concurrency: int,
) -> dict[int, ClusterReview]:
    """Review clusters via batch_and_run; clusters it cannot review are left unchanged."""
    results, unprocessable = await batch_and_run(
        pd.DataFrame(rows),
        CLUSTER_REVIEW,
        llm,
        output_model=ClusterList,
        batch_size=batch_size,
        integrity_check=True,
        question=question,
        system_prompt=system_prompt,
        concurrency=concurrency,
    )
    if not unprocessable.empty:
        logger.warning(f"Could not review {len(unprocessable)} clusters this round")

    reviews = {}
    for row in results.itertuples():
        reviews[int(row.response_id)] = ClusterReview(
            response_id=int(row.response_id),
            removed_concept_ids=list(row.removed_concept_ids),
            added_concept_ids=list(row.added_concept_ids),
        )
    return reviews


async def _review_round(
    df: pd.DataFrame,
    llm: LLM,
    question: str,
    system_prompt: str,
    config: ConceptClusteringConfig,
    concurrency: int,
    round_number: int,
) -> tuple[int, int]:
    """Run one review round in place. Returns (concepts removed, concepts added)."""
    centroids = _centroids(df)
    rows = _build_review_rows(df, centroids, config)
    reviews = await _run_cluster_reviews(
        rows, llm, question, system_prompt, config.review_batch_size, concurrency
    )

    index_of = dict(zip(df["concept_id"], df.index))
    removed = 0
    claims: dict[int, list[int]] = {}
    for row in rows:
        cluster_id = row["response_id"]
        review = reviews.get(cluster_id)
        if review is None:
            continue
        member_ids = {m["concept_id"] for m in row["members"]}
        candidate_ids = {c["concept_id"] for c in row["candidates"]}

        to_remove = [
            i for i in dict.fromkeys(review.removed_concept_ids) if i in member_ids
        ]
        to_add = [
            i for i in dict.fromkeys(review.added_concept_ids) if i in candidate_ids
        ]
        ignored = len(review.removed_concept_ids) + len(review.added_concept_ids)
        ignored -= len(to_remove) + len(to_add)
        if ignored > 0:
            logger.warning(
                f"Cluster {cluster_id}: ignored {ignored} concept ids not shown"
            )

        for concept_id in to_remove:
            index = index_of[concept_id]
            df.loc[index, "cluster_id"] = pd.NA
            df.at[index, "rejected_from"].append(cluster_id)
            df.at[index, "history"].append(
                f"round {round_number}: removed from cluster {cluster_id}"
            )
            removed += 1
        for concept_id in to_add:
            claims.setdefault(concept_id, []).append(cluster_id)

    added = 0
    for concept_id, claimed_by in claims.items():
        index = index_of[concept_id]
        embedding = df.at[index, "embedding"]
        winner = max(
            claimed_by, key=lambda cid: float(np.dot(embedding, centroids[cid]))
        )
        df.loc[index, "cluster_id"] = winner
        df.at[index, "history"].append(
            f"round {round_number}: added to cluster {winner}"
        )
        added += 1

    _dissolve_small_clusters(df, config.min_cluster_size, round_number)
    return removed, added


def _dissolve_small_clusters(
    df: pd.DataFrame, min_size: int, round_number: int
) -> None:
    """Return under-supported clusters to the pool so they can be absorbed elsewhere."""
    clustered = df[df["cluster_id"].notna()]
    support = clustered.groupby("cluster_id")["source_response_id"].nunique()
    for cluster_id in support[support < min_size].index:
        for index in df.index[df["cluster_id"] == cluster_id]:
            df.loc[index, "cluster_id"] = pd.NA
            df.at[index, "history"].append(
                f"round {round_number}: cluster {int(cluster_id)} dissolved"
            )


async def _log_near_duplicate_themes(
    themes_df: pd.DataFrame, embedder: Embedder
) -> None:
    """Flag near-identical final themes; merging them is left to a human or a later step."""
    if len(themes_df) < 2:
        return
    embeddings = _normalise(await embedder.aembed(themes_df["topic"].tolist()))
    similarity = embeddings @ embeddings.T
    for i in range(len(themes_df)):
        for j in range(i + 1, len(themes_df)):
            if similarity[i, j] > NEAR_DUPLICATE_SIMILARITY:
                logger.warning(
                    f"Near-duplicate themes ({similarity[i, j]:.2f}): "
                    f"{themes_df['topic'].iat[i]!r} and {themes_df['topic'].iat[j]!r}"
                )
