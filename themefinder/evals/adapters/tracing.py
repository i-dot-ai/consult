"""Trace a run on whichever platform has a connection, or on none.

``resolve_backends`` picks the tracer from the credentials present, so a run
traces whenever a connection is available and stays silent otherwise, and the
callers never name the platform.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from typing import Any, Protocol

from utils import langfuse as langfuse_utils
from utils.langfuse import LangfuseContext


class TracerPort(Protocol):
    def span(self, name: str) -> AbstractContextManager[Any]:
        """Open a parent span that the LLM calls made inside it nest under."""

    def observe(self, llm: Any) -> None:
        """Make the LLM record its calls on this tracer, if it is able to."""


class NoopTracer:
    def span(self, name: str) -> AbstractContextManager[None]:
        del name
        return nullcontext()

    def observe(self, llm: Any) -> None:
        del llm


class LangfuseTracer:
    def __init__(self, context: LangfuseContext):
        self.context = context

    def span(self, name: str) -> AbstractContextManager[Any]:
        return langfuse_utils.trace_context(self.context, name=name)

    def observe(self, llm: Any) -> None:
        # Only an LLM that exposes a client slot (OpenAILLM) can record generations.
        if hasattr(llm, "langfuse_client"):
            llm.langfuse_client = self.context.client


TRACER_FACTORIES: dict[str, Callable[[Any], TracerPort]] = {
    "langfuse": LangfuseTracer,
}
