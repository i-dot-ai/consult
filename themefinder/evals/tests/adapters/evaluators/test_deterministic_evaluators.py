"""Tests for the non-LLM evaluator adapters: MappingF1Evaluator (deterministic,
sklearn) and RedundancyEvaluator (embedding-based, sentence-transformers).

The five LLM-judge evaluators (GroundednessEvaluator, CoverageEvaluator,
TitleSpecificityEvaluator, CondensationQualityEvaluator,
RefinementQualityEvaluator) are covered separately — they need a fake judge
LLM, not the plain fixtures here.
"""

import sys
import types

import adapters.evaluators.redundancy as redundancy_module
import pytest
from adapters.evaluators.mapping_f1 import MappingF1Evaluator
from adapters.evaluators.redundancy import RedundancyEvaluator
from conftest import make_case
from eval_types import Score


class TestMappingF1Evaluator:
    async def test_perfect_match_scores_one(self):
        """Identical expected and predicted mappings score f1 = 1.0."""
        case = make_case(expected_output={"mappings": {"r1": ["a", "b"], "r2": ["c"]}})
        output = {"labels": {"r1": ["a", "b"], "r2": ["c"]}}

        scores = await MappingF1Evaluator().evaluate(case, output)

        assert scores == [Score("f1_score", 1.0, "Evaluated on 2 responses")]

    async def test_complete_mismatch_scores_zero(self):
        """Disjoint expected and predicted labels score f1 = 0.0."""
        case = make_case(expected_output={"mappings": {"r1": ["a"]}})
        output = {"labels": {"r1": ["b"]}}

        scores = await MappingF1Evaluator().evaluate(case, output)

        assert scores[0].name == "f1_score"
        assert scores[0].value == 0.0

    async def test_missing_response_in_output_treated_as_empty_prediction(self):
        """A response absent from the output counts as an empty prediction (f1 = 0)."""
        case = make_case(expected_output={"mappings": {"r1": ["a"], "r2": ["b"]}})
        output = {"labels": {"r1": ["a"]}}  # r2 has no prediction at all

        scores = await MappingF1Evaluator().evaluate(case, output)

        # r1: perfect (f1=1.0), r2: nothing predicted (f1=0.0) -> samples average 0.5
        assert scores[0].value == 0.5

    async def test_no_expected_mappings_short_circuits(self):
        """No expected mappings short-circuits to a 0.0 score with an explanatory comment."""
        case = make_case(expected_output=None)
        output = {"labels": {"r1": ["a"]}}

        scores = await MappingF1Evaluator().evaluate(case, output)

        assert scores == [Score("f1_score", 0.0, "No expected mappings")]

    async def test_bad_output_falls_back_to_zero_score(self):
        """Bad output (None) hits the shared error boundary and degrades to a 0.0 Score."""
        case = make_case(expected_output={"mappings": {"r1": ["a"]}})

        scores = await MappingF1Evaluator().evaluate(case, None)

        assert len(scores) == 1
        assert scores[0].name == "f1_score"
        assert scores[0].value == 0.0
        assert scores[0].comment.startswith("Error:")


class TestRedundancyEvaluatorWithoutModel:
    """Behaviour that never touches sentence-transformers, so these always
    run regardless of whether the optional `eval` extra is installed."""

    async def test_fewer_than_two_titles_short_circuits(self):
        """Fewer than two themes means no pairs to compare, so redundancy is 0.0."""
        case = make_case()
        output = {"themes": {"Only one theme": "desc"}}

        scores = await RedundancyEvaluator().evaluate(case, output)

        assert scores == [Score("redundancy", 0.0, "0/0 pairs above threshold")]

    async def test_no_themes_short_circuits(self):
        """No themes short-circuits to a 0.0 redundancy score."""
        case = make_case()

        scores = await RedundancyEvaluator().evaluate(case, {"themes": {}})

        assert scores == [Score("redundancy", 0.0, "0/0 pairs above threshold")]

    async def test_missing_library_degrades_gracefully(self, monkeypatch):
        """A missing sentence-transformers install degrades to a 0.0 score, not a crash."""

        def _raise_import_error():
            raise ImportError("sentence-transformers not installed")

        monkeypatch.setattr(
            redundancy_module, "_get_sentence_model", _raise_import_error
        )
        case = make_case()
        output = {"themes": {"A": "desc", "B": "desc"}}

        scores = await RedundancyEvaluator().evaluate(case, output)

        assert scores == [Score("redundancy", 0.0, "0/0 pairs above threshold")]


@pytest.fixture
def patched_similarity(monkeypatch):
    """Patch the embedding model and `cos_sim` so RedundancyEvaluator's own
    logic — pairing, thresholding, ratio/rounding, comment formatting — can
    be tested directly. These tests control `cos_sim`'s output outright
    rather than deriving it from real (or hand-rolled) embedding math:
    whether cosine similarity itself is computed correctly is
    sentence-transformers' job to test, not ours. Neither the real package
    nor torch needs to be installed for these tests to run.

    `cos_sim` is imported locally inside `_calculate_redundancy_score`
    (`from sentence_transformers.util import cos_sim`), so there's nothing
    already-imported for `monkeypatch.setattr` to patch when the real
    package isn't installed — this injects a fake module into
    `sys.modules["sentence_transformers.util"]` instead. Python's import
    system checks `sys.modules` for that exact dotted name before ever
    touching the real package, so the local import resolves to this fake
    regardless of whether sentence-transformers is actually installed.

    Returns an object with `.set_matrix(matrix)` and `.model` (the fake
    model, whose `.encode_calls` records each call's titles — for wiring
    assertions, separate from the similarity-math tests below).
    """
    state: dict[str, list[list[float]]] = {}

    class _FakeModel:
        def __init__(self):
            self.encode_calls: list[list[str]] = []

        def encode(self, titles, convert_to_tensor=True):
            self.encode_calls.append(list(titles))
            return titles

    fake_model = _FakeModel()
    monkeypatch.setattr(redundancy_module, "_get_sentence_model", lambda: fake_model)

    fake_util = types.ModuleType("sentence_transformers.util")
    fake_util.cos_sim = lambda a, b: state["matrix"]
    monkeypatch.setitem(sys.modules, "sentence_transformers.util", fake_util)

    def _set_matrix(matrix: list[list[float]]) -> None:
        state["matrix"] = matrix

    return types.SimpleNamespace(set_matrix=_set_matrix, model=fake_model)


class TestRedundancyEvaluatorWithModel:
    async def test_flags_pairs_above_threshold(self, patched_similarity):
        """Pairs above the similarity threshold are counted and named in the comment."""
        # A~B similar (0.9, flagged), A~C and B~C dissimilar (0.1)
        patched_similarity.set_matrix(
            [
                [1.0, 0.9, 0.1],
                [0.9, 1.0, 0.1],
                [0.1, 0.1, 1.0],
            ]
        )
        case = make_case()
        output = {"themes": {"A": "desc", "B": "desc", "C": "desc"}}

        scores = await RedundancyEvaluator(threshold=0.85).evaluate(case, output)

        assert len(scores) == 1
        score = scores[0]
        assert score.name == "redundancy"
        assert score.value == round(1 / 3, 2)
        assert "1/3 pairs above threshold" in score.comment
        assert "A ↔ B (0.9)" in score.comment

    async def test_no_pairs_above_threshold(self, patched_similarity):
        """No pair above the threshold scores 0.0."""
        patched_similarity.set_matrix([[1.0, 0.1], [0.1, 1.0]])
        case = make_case()
        output = {"themes": {"A": "desc", "B": "desc"}}

        scores = await RedundancyEvaluator(threshold=0.85).evaluate(case, output)

        assert scores == [Score("redundancy", 0.0, "0/1 pairs above threshold")]

    async def test_respects_custom_threshold(self, patched_similarity):
        """A custom threshold changes which pairs count as redundant."""
        patched_similarity.set_matrix([[1.0, 0.5], [0.5, 1.0]])
        case = make_case()
        output = {"themes": {"A": "desc", "B": "desc"}}

        scores = await RedundancyEvaluator(threshold=0.4).evaluate(case, output)

        assert scores[0].value == 1.0
        assert "1/1 pairs above threshold" in scores[0].comment

    async def test_encode_called_with_extracted_titles(self, patched_similarity):
        """Wiring: the titles extracted from the output themes are what reach `.encode()`."""
        patched_similarity.set_matrix([[1.0, 0.1], [0.1, 1.0]])
        case = make_case()
        output = {"themes": {"A": "desc", "B": "desc"}}

        await RedundancyEvaluator().evaluate(case, output)

        assert patched_similarity.model.encode_calls == [["A", "B"]]
