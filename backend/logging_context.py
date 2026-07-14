import structlog
from django.conf import settings


def get_context_id() -> str | None:
    """Read the context_id currently bound to the logger, to propagate into an enqueued job."""
    return structlog.contextvars.get_contextvars().get("context_id")


def rebind_context(context_id: str | None = None) -> None:
    """Reset the logger context (clears stale fields from any previous job on this worker),
    then rebind context_id to a propagated value if one was given."""
    settings.LOGGER.refresh_context()
    if context_id:
        settings.LOGGER.set_context_field("context_id", context_id)
