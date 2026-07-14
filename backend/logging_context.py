import uuid

import structlog
from django.conf import settings


def get_or_create_context_id() -> str:
    """Read the context_id currently bound to the logger, to propagate into an enqueued job.

    Mints and binds a fresh one if nothing is bound yet, so callers always get a real,
    stable id -- and so it sticks for the rest of this thread/process's ambient context,
    rather than every downstream consumer independently minting its own when nothing
    was ever bound. There's no non-destructive way to mint just a context_id via the
    logger itself (refresh_context() would wipe any other fields already bound), so
    this mints one the same way the library does internally and binds it via
    set_context_field, consistent with rebind_context below."""
    context_id = structlog.contextvars.get_contextvars().get("context_id")
    if not context_id:
        context_id = str(uuid.uuid4())
        settings.LOGGER.set_context_field("context_id", context_id)
    return context_id


def rebind_context(context_id: str | None = None) -> None:
    """Reset the logger context (clears stale fields from any previous job on this worker),
    then rebind context_id to a propagated value if one was given."""
    settings.LOGGER.refresh_context()
    if context_id:
        settings.LOGGER.set_context_field("context_id", context_id)
