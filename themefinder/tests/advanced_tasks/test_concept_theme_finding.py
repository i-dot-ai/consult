"""Tests for concept-based theme finding."""

import ast
import zlib

import numpy as np
import pandas as pd
import pytest

from themefinder import (
    ConceptClusteringConfig,
    embed_and_cluster_concepts,
    extract_concepts,
    find_themes_via_concepts,
    get_outliers,
    refine_cluster_themes,
    review_clusters,
)
from themefinder.llm import LLMResponse
from themefinder.models import (
    ClusterList,
    ClusterReview,
    ClusterTheme,
    ClusterThemeResponses,
    Concept,
    ConceptExtractionResponses,
    Position,
    ResponseConcepts,
)
from themefinder.tasks import assign_sequential_topic_ids

CONFIG = ConceptClusteringConfig(distance_threshold=0.3, min_cluster_size=3)

# Hand-placed 2D "embeddings" so cosine distances are predictable: group A points
# the same way as (1, 0), group B as (0, 1), and so on.
A_VECTORS = {"a1": (1, 0), "a2": (1, 0.05), "a3": (1, -0.05)}
B_VECTORS = {"b1": (0, 1), "b2": (0.05, 1), "b3": (-0.05, 1)}
C_VECTORS = {"c1": (-1, -0.1), "c2": (-1, -0.15), "c3": (-1, -0.05)}
# Close enough to A to be clustered with it, and a plausible candidate for B.
MISPLACED = {"m": (1, 0.9)}
LONE = {"d": (0.3, -1)}


@pytest.fixture(autouse=True)
def offline_tokenizer(monkeypatch):
    """Avoid tiktoken downloading its vocabulary in tests."""
    monkeypatch.setattr(
        "themefinder.llm_batch_processor.calculate_string_token_length",
        lambda text, model=None: len(text.split()),
    )


class FakeEmbedder:
    """Looks vectors up by text, falling back to a deterministic hash-seeded vector."""

    def __init__(self, *vector_groups):
        self.vectors = {k: v for group in vector_groups for k, v in group.items()}

    async def aembed(self, texts):
        rows = []
        for text in texts:
            if text in self.vectors:
                rows.append(self.vectors[text])
            else:
                rng = np.random.default_rng(zlib.crc32(text.encode()))
                rows.append(rng.normal(size=2))
        return np.asarray(rows, dtype=np.float32)


class ScriptedLLM:
    """Returns whatever the handler registered for the requested output model."""

    def __init__(self, handlers):
        self.handlers = handlers
        self.calls = []

    async def ainvoke(self, prompt, output_model=None):
        self.calls.append(output_model)
        return LLMResponse(parsed=self.handlers[output_model](prompt))


def parse_section(prompt, marker):
    return ast.literal_eval(prompt.rsplit(marker, 1)[1])


def review_handler(remove_texts=(), add_texts=(), seen=None):
    def handle(prompt):
        clusters = parse_section(prompt, "CLUSTERS:\n")
        reviews = []
        for cluster in clusters:
            if seen is not None:
                seen.append(cluster)
            reviews.append(
                ClusterReview(
                    response_id=cluster["response_id"],
                    removed_concept_ids=[
                        m["concept_id"]
                        for m in cluster["members"]
                        if m["text"] in remove_texts
                    ],
                    added_concept_ids=[
                        c["concept_id"]
                        for c in cluster["candidates"]
                        if c["text"] in add_texts
                    ],
                )
            )
        return ClusterList(responses=reviews)

    return handle


def theme_handler(prompt):
    clusters = parse_section(prompt, "CLUSTERS:\n")
    return ClusterThemeResponses(
        responses=[
            ClusterTheme(
                response_id=c["response_id"],
                topic=f"Label {c['response_id']}: One sentence about it.",
            )
            for c in clusters
        ]
    )


def make_concepts(*vector_groups, response_ids=None):
    """Concepts DataFrame, one source response per concept unless response_ids says otherwise."""
    texts = [t for group in vector_groups for t in group]
    response_ids = response_ids or {t: i + 1 for i, t in enumerate(texts)}
    return pd.DataFrame(
        {
            "concept_id": range(1, len(texts) + 1),
            "source_response_id": [response_ids[t] for t in texts],
            "text": texts,
            "position": "AGREEMENT",
        }
    )


def cluster_of(df, text):
    value = df.loc[df["text"] == text, "cluster_id"].iat[0]
    return None if pd.isna(value) else int(value)


async def clustered(*vector_groups, config=CONFIG, response_ids=None):
    embedder = FakeEmbedder(*vector_groups)
    concepts = make_concepts(*vector_groups, response_ids=response_ids)
    return await embed_and_cluster_concepts(concepts, embedder, config)


@pytest.mark.asyncio
async def test_extract_concepts_keeps_source_response_ids():
    def extract(prompt):
        responses = parse_section(prompt, "RESPONSES:\n")
        return ConceptExtractionResponses(
            responses=[
                ResponseConcepts(
                    response_id=r["response_id"],
                    concepts=[
                        Concept(
                            text=f"{r['response']} one", position=Position.AGREEMENT
                        ),
                        Concept(
                            text=f"{r['response']} two", position=Position.DISAGREEMENT
                        ),
                    ],
                )
                for r in responses
            ]
        )

    llm = ScriptedLLM({ConceptExtractionResponses: extract})
    responses_df = pd.DataFrame({"response_id": [10, 11], "response": ["x", "y"]})

    concepts, unprocessable = await extract_concepts(responses_df, llm, "Q?")

    assert concepts["concept_id"].tolist() == [1, 2, 3, 4]
    assert concepts["source_response_id"].tolist() == [10, 10, 11, 11]
    assert concepts["position"].tolist() == ["AGREEMENT", "DISAGREEMENT"] * 2
    assert unprocessable.empty


@pytest.mark.asyncio
async def test_extract_concepts_allows_responses_without_concepts():
    def extract(prompt):
        responses = parse_section(prompt, "RESPONSES:\n")
        return ConceptExtractionResponses(
            responses=[
                ResponseConcepts(
                    response_id=r["response_id"],
                    concepts=[]
                    if r["response"] == "no comment"
                    else [Concept(text="an idea", position=Position.UNCLEAR)],
                )
                for r in responses
            ]
        )

    llm = ScriptedLLM({ConceptExtractionResponses: extract})
    responses_df = pd.DataFrame(
        {"response_id": [1, 2], "response": ["no comment", "something"]}
    )

    concepts, _ = await extract_concepts(responses_df, llm, "Q?")

    assert concepts["source_response_id"].tolist() == [2]


@pytest.mark.asyncio
async def test_initial_clustering_groups_and_pools_small_clusters():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED, LONE)

    assert cluster_of(df, "a1") == cluster_of(df, "a2") == cluster_of(df, "a3")
    assert cluster_of(df, "m") == cluster_of(df, "a1")
    assert cluster_of(df, "b1") == cluster_of(df, "b2") == cluster_of(df, "b3")
    assert cluster_of(df, "b1") != cluster_of(df, "a1")
    assert cluster_of(df, "d") is None


@pytest.mark.asyncio
async def test_cluster_size_counts_distinct_source_responses():
    """Three concepts from one respondent are not enough support for a cluster."""
    same_respondent = {t: 1 for t in A_VECTORS}
    df = await clustered(A_VECTORS, response_ids=same_respondent)

    assert df["cluster_id"].isna().all()


@pytest.mark.asyncio
async def test_review_removes_misplaced_concept_then_adds_it_elsewhere():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED)
    assert cluster_of(df, "m") == cluster_of(df, "a1")
    llm = ScriptedLLM(
        {ClusterList: review_handler(remove_texts={"m"}, add_texts={"m"})}
    )

    result = await review_clusters(df, llm, "Q?", config=CONFIG)

    assert cluster_of(result, "m") == cluster_of(result, "b1")
    assert (
        cluster_of(result, "a1") == cluster_of(result, "a2") == cluster_of(result, "a3")
    )
    history = result.loc[result["text"] == "m", "history"].iat[0]
    assert any("removed from cluster" in event for event in history)
    assert any("added to cluster" in event for event in history)


@pytest.mark.asyncio
async def test_removed_concept_is_never_offered_back_to_the_same_cluster():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED)
    a_cluster = cluster_of(df, "a1")
    seen = []
    llm = ScriptedLLM(
        {ClusterList: review_handler(remove_texts={"m"}, add_texts=set(), seen=seen)}
    )
    config = ConceptClusteringConfig(
        distance_threshold=0.3, min_cluster_size=3, max_review_rounds=4, min_progress=0
    )

    result = await review_clusters(df, llm, "Q?", config=config)

    offered_to_a = [
        c["text"]
        for cluster in seen
        if cluster["response_id"] == a_cluster
        for c in cluster["candidates"]
    ]
    assert "m" not in offered_to_a
    assert a_cluster in result.loc[result["text"] == "m", "rejected_from"].iat[0]


@pytest.mark.asyncio
async def test_review_conserves_every_concept():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED, LONE)
    llm = ScriptedLLM(
        {ClusterList: review_handler(remove_texts={"m"}, add_texts={"m", "d"})}
    )

    result = await review_clusters(df, llm, "Q?", config=CONFIG)

    assert sorted(result["concept_id"]) == sorted(df["concept_id"])
    assert result["concept_id"].is_unique
    assert len(result) == len(df)


@pytest.mark.asyncio
async def test_review_does_not_mutate_its_input():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED)
    clusters_before = df["cluster_id"].copy()
    history_before = [list(h) for h in df["history"]]
    llm = ScriptedLLM({ClusterList: review_handler(remove_texts={"m"})})

    await review_clusters(df, llm, "Q?", config=CONFIG)

    assert df["cluster_id"].equals(clusters_before)
    assert [list(h) for h in df["history"]] == history_before
    assert all(not rejected for rejected in df["rejected_from"])


@pytest.mark.asyncio
async def test_conflicting_additions_go_to_the_nearest_centroid():
    df = await clustered(A_VECTORS, B_VECTORS, MISPLACED)
    df.loc[df["text"] == "m", "cluster_id"] = pd.NA
    llm = ScriptedLLM({ClusterList: review_handler(add_texts={"m"})})

    result = await review_clusters(df, llm, "Q?", config=CONFIG)

    # m is nearer to A's centroid than B's, although both clusters claim it.
    assert cluster_of(result, "m") == cluster_of(result, "a1")


@pytest.mark.asyncio
async def test_ids_the_llm_was_not_shown_are_ignored():
    df = await clustered(A_VECTORS, B_VECTORS)
    b_id = cluster_of(df, "b1")
    a_member_ids = df.loc[df["text"].isin(A_VECTORS), "concept_id"].tolist()

    def bogus(prompt):
        clusters = parse_section(prompt, "CLUSTERS:\n")
        return ClusterList(
            responses=[
                ClusterReview(
                    response_id=c["response_id"],
                    removed_concept_ids=[999],
                    # an A member offered as an addition to B, where it was never a candidate
                    added_concept_ids=a_member_ids if c["response_id"] == b_id else [],
                )
                for c in clusters
            ]
        )

    result = await review_clusters(
        df, ScriptedLLM({ClusterList: bogus}), "Q?", config=CONFIG
    )

    assert (
        result["cluster_id"].astype(object).tolist()
        == df["cluster_id"].astype(object).tolist()
    )


@pytest.mark.asyncio
async def test_loop_stops_when_a_round_makes_no_progress():
    df = await clustered(A_VECTORS, B_VECTORS, LONE)
    llm = ScriptedLLM({ClusterList: review_handler()})

    await review_clusters(df, llm, "Q?", config=CONFIG)

    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_loop_stops_at_max_review_rounds():
    df = await clustered(A_VECTORS, B_VECTORS, LONE)
    llm = ScriptedLLM({ClusterList: review_handler()})
    config = ConceptClusteringConfig(
        distance_threshold=0.3, min_cluster_size=3, min_progress=0, max_review_rounds=2
    )

    await review_clusters(df, llm, "Q?", config=config)

    assert len(llm.calls) == 2


@pytest.mark.asyncio
async def test_loop_stops_once_the_pool_is_small_enough():
    df = await clustered(A_VECTORS, B_VECTORS, LONE)
    llm = ScriptedLLM({ClusterList: review_handler()})
    config = ConceptClusteringConfig(
        distance_threshold=0.3,
        min_cluster_size=3,
        min_progress=0,
        max_review_rounds=5,
        leftover_target_fraction=0.5,
    )

    await review_clusters(df, llm, "Q?", config=config)

    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_failed_review_batches_change_nothing():
    df = await clustered(A_VECTORS, B_VECTORS, LONE)

    def failing(prompt):
        raise ValueError("bad structured output")

    llm = ScriptedLLM({ClusterList: failing})

    result = await review_clusters(df, llm, "Q?", config=CONFIG)

    assert (
        result["cluster_id"].astype(object).tolist()
        == df["cluster_id"].astype(object).tolist()
    )


@pytest.mark.asyncio
async def test_final_leftover_clustering_forms_clusters_and_keeps_outliers():
    df = await clustered(A_VECTORS, B_VECTORS, C_VECTORS, LONE)
    assert cluster_of(df, "c1") is not None
    df.loc[df["text"].isin(C_VECTORS), "cluster_id"] = pd.NA
    llm = ScriptedLLM({ClusterList: review_handler()})
    config = ConceptClusteringConfig(
        distance_threshold=0.3, min_cluster_size=3, max_review_rounds=1
    )

    result = await review_clusters(df, llm, "Q?", config=config)

    assert (
        cluster_of(result, "c1") == cluster_of(result, "c2") == cluster_of(result, "c3")
    )
    assert cluster_of(result, "c1") not in {
        cluster_of(result, "a1"),
        cluster_of(result, "b1"),
    }

    outliers = get_outliers(result)
    assert outliers["text"].tolist() == ["d"]
    assert outliers["nearest_cluster_id"].notna().all()
    assert outliers["nearest_cluster_distance"].iat[0] > 0


@pytest.mark.asyncio
async def test_refinement_counts_distinct_responses_and_assigns_ids():
    config = ConceptClusteringConfig(distance_threshold=0.3, min_cluster_size=2)
    # A has three concepts but only two respondents; B has three respondents.
    response_ids = {"a1": 1, "a2": 1, "a3": 2, "b1": 3, "b2": 4, "b3": 5}
    df = await clustered(A_VECTORS, B_VECTORS, config=config, response_ids=response_ids)
    llm = ScriptedLLM({ClusterThemeResponses: theme_handler})

    themes, unprocessable = await refine_cluster_themes(df, llm, "Q?", config=config)

    assert themes["topic_id"].tolist() == ["A", "B"]
    assert themes["source_topic_count"].tolist() == [3, 2]
    assert themes["cluster_id"].tolist() == [cluster_of(df, "b1"), cluster_of(df, "a1")]
    assert themes["topic"].str.contains(": ").all()
    assert set(themes["position"]) == {"AGREEMENT"}
    assert unprocessable.empty


@pytest.mark.asyncio
async def test_refinement_with_no_clusters_returns_empty_themes():
    df = await clustered(LONE)

    themes, _ = await refine_cluster_themes(df, ScriptedLLM({}), "Q?", config=CONFIG)

    assert themes.empty
    assert "topic_id" in themes.columns


@pytest.mark.asyncio
async def test_find_themes_via_concepts_end_to_end():
    by_response = {
        1: ["a1", "b1"],
        2: ["a2"],
        3: ["a3"],
        4: ["b2"],
        5: ["b3"],
        6: ["d"],
    }

    def extract(prompt):
        responses = parse_section(prompt, "RESPONSES:\n")
        return ConceptExtractionResponses(
            responses=[
                ResponseConcepts(
                    response_id=r["response_id"],
                    concepts=[
                        Concept(text=t, position=Position.AGREEMENT)
                        for t in by_response[r["response_id"]]
                    ],
                )
                for r in responses
            ]
        )

    llm = ScriptedLLM(
        {
            ConceptExtractionResponses: extract,
            ClusterList: review_handler(),
            ClusterThemeResponses: theme_handler,
        }
    )
    embedder = FakeEmbedder(A_VECTORS, B_VECTORS, LONE)
    responses_df = pd.DataFrame(
        {
            "response_id": list(by_response),
            "response": [f"response {i}" for i in by_response],
        }
    )

    result = await find_themes_via_concepts(
        responses_df, llm, embedder, "Q?", config=CONFIG
    )

    assert len(result["themes"]) == 2
    assert result["themes"]["source_topic_count"].tolist() == [3, 3]
    assert result["outliers"]["text"].tolist() == ["d"]
    assert "embedding" not in result["concepts"].columns
    assert len(result["concepts"]) == 7
    assert result["question"] == "Q?"
    assert result["unprocessables"].empty


@pytest.mark.asyncio
async def test_find_themes_via_concepts_handles_no_concepts():
    def extract(prompt):
        responses = parse_section(prompt, "RESPONSES:\n")
        return ConceptExtractionResponses(
            responses=[
                ResponseConcepts(response_id=r["response_id"]) for r in responses
            ]
        )

    llm = ScriptedLLM({ConceptExtractionResponses: extract})
    responses_df = pd.DataFrame({"response_id": [1], "response": ["no comment"]})

    result = await find_themes_via_concepts(
        responses_df, llm, FakeEmbedder(), "Q?", config=CONFIG
    )

    assert result["themes"].empty
    assert result["outliers"].empty


def test_cluster_theme_requires_label_and_description():
    with pytest.raises(ValueError):
        ClusterTheme(response_id=1, topic="no colon here")
    with pytest.raises(ValueError):
        ClusterTheme(response_id=1, topic="label only:   ")

    assert ClusterTheme(response_id=1, topic="Label: A sentence.").topic


def test_cluster_theme_responses_rejects_duplicate_cluster_ids():
    theme = ClusterTheme(response_id=1, topic="Label: A sentence.")

    with pytest.raises(ValueError):
        ClusterThemeResponses(responses=[theme, theme])


def test_concept_rejects_blank_text():
    with pytest.raises(ValueError):
        Concept(text="   ", position=Position.AGREEMENT)


def test_assign_sequential_topic_ids_rolls_over_after_z():
    df = assign_sequential_topic_ids(pd.DataFrame({"x": range(28)}))

    assert df["topic_id"].iat[0] == "A"
    assert df["topic_id"].iat[25] == "Z"
    assert df["topic_id"].iat[26] == "AA"
    assert df["topic_id"].iat[27] == "AB"
