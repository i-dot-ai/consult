"""Markdown prompt templates, loaded by name so prompts stay editable as plain text."""

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def _read(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def load_prompt_fn(name: str) -> Callable[..., str]:
    """Return a function rendering `<name>.md` from keyword args.

    Substitutes `{key}` literally rather than using `str.format`, so prompts
    can contain raw JSON braces without escaping.
    """
    template = _read(name)

    def prompt_fn(**kwargs) -> str:
        prompt = template
        for key, value in kwargs.items():
            prompt = prompt.replace("{" + key + "}", str(value))
        return prompt

    return prompt_fn
