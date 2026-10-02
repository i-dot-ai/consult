"""Utilities for loading prompt templates from markdown files."""

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Load a prompt template from the synthetic prompts directory."""
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")
