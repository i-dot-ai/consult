"""RedundancyEvaluator — semantic redundancy among generated theme titles.

Embedding-based (sentence-transformers), no LLM call. Ignores `case` entirely —
only scores `output["themes"]`, matching today's `create_redundancy_evaluator`.
"""

import logging
from functools import lru_cache
from typing import Any

from eval_types import Case, Score

from .base import EvaluatorPort

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_sentence_model():
    """Load and cache the sentence-transformers model (loaded once per process)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


class RedundancyEvaluator(EvaluatorPort):
    metric_names = ("redundancy",)

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def _calculate_redundancy_score(self, themes: list[dict] | dict) -> dict[str, Any]:
        """Compute pairwise cosine similarity between theme titles, flagging
        pairs above `self.threshold`."""
        try:
            _get_sentence_model()
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, skipping redundancy check"
            )
            return {
                "ratio": 0.0,
                "n_redundant_pairs": 0,
                "n_total_pairs": 0,
                "flagged_pairs": [],
            }

        titles = self.extract_theme_titles(themes)

        if len(titles) < 2:
            return {
                "ratio": 0.0,
                "n_redundant_pairs": 0,
                "n_total_pairs": 0,
                "flagged_pairs": [],
            }

        model = _get_sentence_model()
        embeddings = model.encode(titles, convert_to_tensor=True)

        from sentence_transformers.util import cos_sim

        similarity_matrix = cos_sim(embeddings, embeddings)

        flagged_pairs = []
        n_total_pairs = 0

        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                n_total_pairs += 1
                sim = float(similarity_matrix[i][j])
                if sim >= self.threshold:
                    flagged_pairs.append(
                        {
                            "theme_a": titles[i],
                            "theme_b": titles[j],
                            "similarity": round(sim, 3),
                        }
                    )

        ratio = len(flagged_pairs) / n_total_pairs if n_total_pairs > 0 else 0.0

        return {
            "ratio": ratio,
            "n_redundant_pairs": len(flagged_pairs),
            "n_total_pairs": n_total_pairs,
            "flagged_pairs": flagged_pairs,
        }

    async def _score(self, case: Case, output: Any) -> list[Score]:
        result = self._calculate_redundancy_score(output.get("themes", []))

        comment = f"{result['n_redundant_pairs']}/{result['n_total_pairs']} pairs above threshold"
        if result["flagged_pairs"]:
            pair_strs = [
                f"  {p['theme_a']} ↔ {p['theme_b']} ({p['similarity']})"
                for p in result["flagged_pairs"]
            ]
            comment += "\n" + "\n".join(pair_strs)

        return [Score("redundancy", round(result["ratio"], 2), comment)]
