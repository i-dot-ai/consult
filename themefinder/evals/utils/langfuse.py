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
    handler: None = None  # Retained for API compatibility; always None
    session_id: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse is configured and available."""
        return self.client is not None


def enable_openai_tracing(context: LangfuseContext | None) -> bool:
    """Enable Langfuse OpenAI tracing for subsequently created SDK clients.

    This preserves optional generation-level observability for benchmark runs.
    It must be called before creating an ``OpenAILLM`` because the Langfuse
    integration instruments the OpenAI SDK client class. Gateway response
    headers, not Langfuse, remain the source of evaluation metrics.
    """
    if not getattr(context, "is_enabled", False):
        return False

    try:
        import openai
        from langfuse.openai import openai as langfuse_openai
    except ImportError:
        logger.warning("Langfuse OpenAI instrumentation is not available")
        return False

    openai.OpenAI = langfuse_openai.OpenAI
    openai.AsyncOpenAI = langfuse_openai.AsyncOpenAI
    return True


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
        with context.client.start_as_current_span(
            name=name, metadata=context.metadata
        ) as span:
            span.update_trace(
                session_id=context.session_id,
                tags=context.tags,
                metadata=context.metadata,
            )
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

    Updated for Langfuse SDK v3 which changed CallbackHandler API.
    In v3, session_id/tags/metadata are passed via LangChain's config["metadata"]
    using special keys: langfuse_session_id, langfuse_tags, etc.

    Args:
        session_id: Unique identifier for grouping traces
            (e.g., "eval_generation_20260129_120000")
        eval_type: Type of evaluation (e.g., "generation", "sentiment", "mapping")
        metadata: Optional additional metadata dict to merge with standard metadata
        tags: Optional additional tags to merge with standard tags
        settings: EvalSettings to read credentials/env context from; defaults
            to the process-wide eval_settings singleton.

    Returns:
        LangfuseContext with client and handler (or None values if not configured)
    """
    settings = settings or eval_settings
    langfuse_settings = settings.active_langfuse

    if langfuse_settings is None:
        logger.info("Langfuse not configured - tracing disabled")
        return LangfuseContext(client=None, handler=None)

    secret_key = langfuse_settings.secret_key
    public_key = langfuse_settings.public_key
    base_url = langfuse_settings.base_url

    try:
        from langfuse import Langfuse

        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=base_url,
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
            "version": version,
            "git_sha": git_sha,
            "environment": environment,
        }
        all_metadata = {**standard_metadata, **(metadata or {})}

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


def create_scores(
    context: LangfuseContext,
    scores: dict[str, float | int],
    trace_id: str | None = None,
) -> None:
    """Attach computed metrics as scores to the current trace.

    Uses score_current_trace() when inside a trace_context() block,
    otherwise falls back to explicit trace_id attachment.

    Args:
        context: LangfuseContext from get_langfuse_context()
        scores: Dict mapping score names to numeric values
        trace_id: Optional trace_id (used only as fallback)
    """
    if not context.is_enabled or not context.client:
        return

    # No handler fallback — trace_id must be provided explicitly if needed

    for name, value in scores.items():
        if not isinstance(value, (int, float)):
            logger.debug(f"Skipping non-numeric score {name}={value}")
            continue

        try:
            context.client.score_current_trace(
                name=name, value=float(value), data_type="NUMERIC"
            )
            logger.debug(f"Attached score {name}={value} to current trace")
        except Exception:
            if trace_id:
                try:
                    context.client.create_score(
                        name=name,
                        value=float(value),
                        trace_id=trace_id,
                        data_type="NUMERIC",
                    )
                    logger.debug(f"Attached score {name}={value} via trace_id")
                except Exception as e:
                    logger.warning(f"Failed to attach score {name}: {e}")
            else:
                logger.warning(f"Failed to attach score {name}: no trace context")


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


@contextmanager
def dataset_item_trace(
    context: LangfuseContext,
    dataset_item: Any,
    run_name: str,
) -> Generator[tuple[Any, str | None], None, None]:
    """Create a trace for a single dataset item linked to a dataset run.

    Uses Langfuse's item.run() context manager which automatically:
    - Creates a trace linked to the dataset item
    - Associates the trace with a named dataset run
    - Aggregates metadata and costs at the run level

    Args:
        context: LangfuseContext from get_langfuse_context()
        dataset_item: Langfuse dataset item object (must have .run() method)
        run_name: Name of the experiment run (typically session_id)

    Yields:
        Tuple of (span object, trace_id) for score attachment.
        Both are None if Langfuse is disabled.

    Example:
        for item in dataset.items:
            with dataset_item_trace(ctx, item, ctx.session_id) as (trace, trace_id):
                result = await run_task(item)
                if trace:
                    trace.update(output=result)
                if trace_id:
                    ctx.client.create_score(
                        trace_id=trace_id, name="accuracy", value=0.95, data_type="NUMERIC"
                    )
    """
    if not context.is_enabled or not context.client:
        yield None, None
        return

    try:
        with dataset_item.run(
            run_name=run_name,
            run_metadata=context.metadata,
        ) as root_span:
            root_span.update_trace(
                session_id=context.session_id,
                tags=context.tags,
                metadata=context.metadata,
            )
            yield root_span, root_span.trace_id

    except Exception as e:
        logger.warning(f"Failed to create dataset item trace: {e}")
        yield None, None
