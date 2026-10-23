"""Shared sentence-embedding model, so evaluators and run statistics load it once."""

from functools import lru_cache


@lru_cache(maxsize=1)
def get_sentence_model():
    """Load and cache the sentence-transformers model (loaded once per process)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")
