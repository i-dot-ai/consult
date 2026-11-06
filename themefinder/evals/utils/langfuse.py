"""Langfuse integration utilities for ThemeFinder evaluations.

Provides graceful fallback when Langfuse is not configured.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generator

from settings import EvalSettings, eval_settings

from utils.logging_config import get_logger
from utils.masking import mask_sensitive

if TYPE_CHECKING:
    from langfuse import Langfuse
    from langfuse._client.span import LangfuseSpan

logger = get_logger(__name__)


def _get_version() -> str:
    """Get package version from installed metadata.

    Returns:
        Version string (e.g., "0.7.8") or "unknown" if not found.
    """
    try:
        from importlib.metadata import version

        return version("themefinder")
    except Exception:
        return "unknown"


@dataclass
class LangfuseContext:
    """Container for Langfuse client."""

    client: "Langfuse | None"
    session_id: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse is configured and available."""
        return self.client is not None


@contextmanager
def trace_context(
    context: LangfuseContext, name: str = "eval_task"
) -> Generator["LangfuseSpan | None", None, None]:
    """Create a parent Langfuse span for trace-level attributes.

    Args:
        context: LangfuseContext from get_langfuse_context()
        name: Name for the parent span (e.g., "generation_eval", "question_1")

    Yields:
        LangfuseSpan instance (or None if Langfuse is disabled)

    Example:
        with trace_context(langfuse_ctx, name="generation_eval") as span:
            response = llm.invoke(prompt)  # Nested under span with tags/metadata
    """
    if not context.is_enabled or not context.client:
        yield None
        return

    try:
        from langfuse import propagate_attributes

        with (
            context.client.start_as_current_observation(
                name=name, metadata=context.metadata
            ) as span,
            propagate_attributes(
                session_id=context.session_id,
                tags=context.tags,
                metadata=context.metadata,
            ),
        ):
            yield span
    except ImportError:
        logger.warning("Langfuse package not available")
        yield None
    except Exception as e:
        logger.warning(f"Failed to create trace context: {e}")
        yield None


def get_langfuse_context(
    session_id: str,
    eval_type: str,
    metadata: dict | None = None,
    tags: list[str] | None = None,
    settings: EvalSettings | None = None,
) -> LangfuseContext:
    """Initialise Langfuse with structured tags and metadata.

    Langfuse SDK v4 has no CallbackHandler: session_id/tags/metadata are held
    here and applied to traces via propagate_attributes (see trace_context).

    Args:
        session_id: Unique identifier for grouping traces
            (e.g., "eval_generation_20260129_120000")
        eval_type: Type of evaluation (e.g., "generation", "sentiment", "mapping")
        metadata: Optional additional metadata dict to merge with standard metadata
        tags: Optional additional tags to merge with standard tags
        settings: EvalSettings to read credentials/env context from; defaults
            to the process-wide eval_settings singleton.

    Returns:
        LangfuseContext with client (or client=None if not configured)
    """
    settings = settings if settings is not None else eval_settings
    langfuse_settings = settings.active_langfuse

    if langfuse_settings is None:
        logger.info("Langfuse not configured - tracing disabled")
        return LangfuseContext(client=None)

    secret_key = langfuse_settings.secret_key
    public_key = langfuse_settings.public_key
    base_url = langfuse_settings.base_url

    try:
        from langfuse import Langfuse

        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            # v4 ranks the LANGFUSE_BASE_URL env var above host=, so pass base_url
            base_url=base_url,
            mask=mask_sensitive,
        )

        # Build standard tags and metadata
        version = _get_version()
        environment = settings.environment
        git_sha = settings.git_sha
        model = settings.auto_eval_model or "unknown"

        # Build standard tags - note: model tag is only added if not provided
        # by caller (benchmark.py provides its own model tag)
        has_model_tag = any(t.startswith("model:") for t in (tags or []))
        standard_tags = [
            "eval",
            eval_type,
            f"v{version}",
            environment,
        ]
        if not has_model_tag:
            standard_tags.append(f"model:{model}")
        all_tags = standard_tags + (tags or [])

        standard_metadata = {
            "eval_type": eval_type,
            "model": model,
            # Scores are only comparable between runs scored by the same judge
            "judge_model": settings.judge_model,
            "version": version,
            "git_sha": git_sha,
            "environment": environment,
            # Run-level traces and scores override this, so dashboards can filter either way
            "aggregate": "false",
        }
        # v4 propagates only str values, so stringify here to keep dashboard
        # filters identical across entry points; None means "not applicable"
        all_metadata = {
            key: str(value)
            for key, value in {**standard_metadata, **(metadata or {})}.items()
            if value is not None
        }

        logger.info(
            f"Langfuse initialised: session_id={session_id}, "
            f"eval_type={eval_type}, version={version}, env={environment}"
        )
        return LangfuseContext(
            client=client,
            session_id=session_id,
            tags=all_tags,
            metadata=all_metadata,
        )

    except ImportError:
        logger.warning("Langfuse package not available")
        return LangfuseContext(client=None)
    except Exception as e:
        logger.warning(f"Failed to initialise Langfuse: {e}")
        return LangfuseContext(client=None)


def flush(context: LangfuseContext) -> None:
    """Flush pending Langfuse data before exit.

    Args:
        context: LangfuseContext from get_langfuse_context()
    """
    if context.is_enabled and context.client:
        try:
            context.client.flush()
            logger.debug("Langfuse data flushed")
        except Exception as e:
            logger.warning(f"Failed to flush Langfuse: {e}")


def link_dataset_item(
    client: "Langfuse",
    *,
    run_name: str,
    dataset_item_id: str,
    trace_id: str,
    metadata: dict | None = None,
) -> Any:
    """Link a trace to a named dataset run by hand.

    SDK v4 removed DatasetItemClient.run(), and our runners own task execution,
    so the experiment SDK can't do this for us. Errors propagate to the caller.
    """
    return client.api.dataset_run_items.create(
        run_name=run_name,
        dataset_item_id=dataset_item_id,
        trace_id=trace_id,
        metadata=metadata,
    )
