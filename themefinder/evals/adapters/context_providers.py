"""Build the tracing context for each platform, keyed by platform name.

Kept out of config.py so a new tracing platform is one function and one registry
entry, and so whoever creates a context is also the one who closes it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from datasets import DatasetConfig
from settings import EvalSettings
from utils import langfuse as langfuse_utils


@dataclass(frozen=True)
class ProvidedContext:
    """A platform context plus the action that releases it.

    ``close`` is a no-op for caller-supplied contexts, which stay the caller's
    responsibility to flush.
    """

    context: Any
    close: Callable[[], None]


ContextProvider = Callable[[DatasetConfig, EvalSettings, Any | None], ProvidedContext]


def _require_langfuse_context(context: Any | None) -> Any:
    if (
        context is None
        or not getattr(context, "is_enabled", False)
        or getattr(context, "client", None) is None
    ):
        raise ValueError("Langfuse was selected but its context is unavailable.")
    return context


def build_langfuse_context(
    dataset_config: DatasetConfig,
    settings: EvalSettings,
    context: Any | None,
) -> ProvidedContext:
    """Reuse a caller-supplied context, or create one from settings and own it."""
    if context is not None:
        return ProvidedContext(_require_langfuse_context(context), lambda: None)

    if settings.active_langfuse is None:
        raise ValueError(
            "Langfuse requires LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY "
            "and LANGFUSE_BASE_URL, or an enabled caller-supplied context."
        )
    session_id = (
        f"{dataset_config.name.replace('/', '_')}_"
        f"{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid4()}"
    )
    created = _require_langfuse_context(
        langfuse_utils.get_langfuse_context(
            session_id=session_id,
            eval_type=dataset_config.component,
            metadata={"dataset": dataset_config.dataset},
            tags=[dataset_config.dataset],
            settings=settings,
        )
    )
    return ProvidedContext(created, lambda: langfuse_utils.flush(created))


CONTEXT_PROVIDERS: dict[str, ContextProvider] = {
    "langfuse": build_langfuse_context,
}
