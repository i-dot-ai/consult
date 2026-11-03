"""Unit tests for the tracers resolve_backends can hand out."""

from contextlib import contextmanager
from types import SimpleNamespace

from adapters import tracing
from adapters.tracing import LangfuseTracer, NoopTracer
from utils.langfuse import LangfuseContext


class _ObservableLlm:
    langfuse_client = None


def test_noop_tracer_opens_an_empty_span_and_leaves_the_llm_alone():
    tracer = NoopTracer()
    llm = _ObservableLlm()

    with tracer.span("generation_eval") as span:
        tracer.observe(llm)

    assert span is None
    assert llm.langfuse_client is None


def test_langfuse_tracer_span_is_the_context_trace(monkeypatch):
    context = LangfuseContext(client=SimpleNamespace())
    opened = []

    @contextmanager
    def fake_trace_context(trace_context, name):
        opened.append((trace_context, name))
        yield "span"

    monkeypatch.setattr(tracing.langfuse_utils, "trace_context", fake_trace_context)

    with LangfuseTracer(context).span("mapping_eval") as span:
        pass

    assert span == "span"
    assert opened == [(context, "mapping_eval")]


def test_langfuse_tracer_hands_its_client_to_an_llm_that_can_hold_one():
    client = SimpleNamespace()
    tracer = LangfuseTracer(LangfuseContext(client=client))
    observable = _ObservableLlm()
    plain = object()

    tracer.observe(observable)
    tracer.observe(plain)

    assert observable.langfuse_client is client
    assert not hasattr(plain, "langfuse_client")
