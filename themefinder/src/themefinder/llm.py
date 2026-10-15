"""LLM abstraction layer for themefinder.

Provides a Protocol-based interface for LLM calls with structured output support,
and an OpenAI implementation. Designed for easy extension to other providers.
"""

import asyncio
import concurrent.futures
import contextvars
import math
import threading
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx
import openai
from pydantic import BaseModel


@dataclass
class LLMResponse:
    """Wraps an LLM call result."""

    parsed: BaseModel | str


class GatewayMetricsError(RuntimeError):
    """Raised when the LLM gateway does not return its required metric headers."""


@dataclass(frozen=True)
class GatewayCallMetrics:
    """Metrics returned by the gateway for one completed LLM call."""

    cost_usd: float
    latency_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class GatewayMetricsSummary:
    """Totals for the gateway calls made in one active collection scope."""

    call_count: int
    cost_usd: float | None
    latency_seconds: float | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass
class GatewayMetricsCollector:
    """Collect gateway-supplied metrics for the current evaluation run.

    The gateway is the source of truth for cost and request duration. LiteLLM
    defines ``x-litellm-response-cost`` as USD. A lock is used because
    ``OpenAILLM.invoke`` can make its async request in a worker thread.
    """

    _calls: list[GatewayCallMetrics] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, headers: Mapping[str, str], response: Any) -> None:
        """Record one response, rejecting incomplete gateway metric data."""
        cost_usd = _parse_required_metric_header(headers, "x-litellm-response-cost")
        duration_ms = _parse_required_metric_header(
            headers, "x-litellm-response-duration-ms"
        )
        usage = getattr(response, "usage", None)
        call = GatewayCallMetrics(
            cost_usd=cost_usd,
            latency_seconds=duration_ms / 1_000,
            input_tokens=_usage_value(usage, "prompt_tokens", "input_tokens"),
            output_tokens=_usage_value(usage, "completion_tokens", "output_tokens"),
            total_tokens=_usage_value(usage, "total_tokens"),
        )
        with self._lock:
            self._calls.append(call)

    def summary(self) -> GatewayMetricsSummary:
        """Return totals without turning missing values into zeroes."""
        with self._lock:
            calls = tuple(self._calls)

        return GatewayMetricsSummary(
            call_count=len(calls),
            cost_usd=_sum_metric(calls, "cost_usd"),
            latency_seconds=_sum_metric(calls, "latency_seconds"),
            input_tokens=_sum_metric(calls, "input_tokens"),
            output_tokens=_sum_metric(calls, "output_tokens"),
            total_tokens=_sum_metric(calls, "total_tokens"),
        )


_active_gateway_metrics: contextvars.ContextVar[GatewayMetricsCollector | None] = (
    contextvars.ContextVar("active_gateway_metrics", default=None)
)
_gateway_response_headers: contextvars.ContextVar[Mapping[str, str] | None] = (
    contextvars.ContextVar("gateway_response_headers", default=None)
)


@contextmanager
def collect_gateway_metrics() -> Generator[GatewayMetricsCollector, None, None]:
    """Collect gateway metrics for all ``OpenAILLM`` calls in this context.

    Child asyncio tasks inherit the collection context. ``OpenAILLM.invoke``
    explicitly copies it to its worker thread as well.
    """
    collector = GatewayMetricsCollector()
    token = _active_gateway_metrics.set(collector)
    try:
        yield collector
    finally:
        _active_gateway_metrics.reset(token)


def _parse_required_metric_header(headers: Mapping[str, str], name: str) -> float:
    value = headers.get(name)
    if value is None:
        raise GatewayMetricsError(f"LLM gateway response did not include {name}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GatewayMetricsError(
            f"LLM gateway returned an invalid {name}: {value!r}"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise GatewayMetricsError(f"LLM gateway returned an invalid {name}: {value!r}")
    return number


def _usage_value(usage: Any, *names: str) -> int | None:
    if usage is None:
        return None
    for name in names:
        value = getattr(usage, name, None)
        if value is not None:
            return int(value)
    return None


def _sum_metric(
    calls: tuple[GatewayCallMetrics, ...], field_name: str
) -> float | int | None:
    values = [getattr(call, field_name) for call in calls]
    if not values or any(value is None for value in values):
        return None
    return sum(values)


async def _capture_gateway_response_headers(response: httpx.Response) -> None:
    """Keep the current task's gateway response headers for metric collection.

    The OpenAI SDK's parsed response intentionally does not expose HTTP
    headers. Capturing them in an HTTPX response hook lets evaluation calls
    keep the standard SDK response path, which Langfuse instruments correctly.
    """
    if _active_gateway_metrics.get() is not None:
        _gateway_response_headers.set(dict(response.headers))


def _metrics_http_client(*, timeout: Any | None) -> httpx.AsyncClient:
    """Build the HTTP client used by an ``OpenAILLM`` SDK client."""
    kwargs: dict[str, Any] = {
        "event_hooks": {"response": [_capture_gateway_response_headers]},
        "follow_redirects": True,
    }
    if timeout is not None:
        kwargs["timeout"] = timeout
    return httpx.AsyncClient(**kwargs)


def _add_metrics_response_hook(http_client: Any) -> None:
    """Add header capture to a caller-supplied HTTPX client once."""
    response_hooks = http_client.event_hooks.setdefault("response", [])
    if _capture_gateway_response_headers not in response_hooks:
        response_hooks.append(_capture_gateway_response_headers)


@runtime_checkable
class LLM(Protocol):
    """Protocol defining the LLM interface for themefinder."""

    async def ainvoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse: ...

    def invoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse: ...


class OpenAILLM:
    """OpenAI SDK implementation of the LLM protocol."""

    def __init__(
        self,
        model,
        request_kwargs: dict | None = None,
        **client_kwargs,
    ):
        self.model = model
        self.request_kwargs = request_kwargs or {}
        sdk_client_kwargs = dict(client_kwargs)
        supplied_http_client = sdk_client_kwargs.get("http_client")
        if supplied_http_client is not None:
            _add_metrics_response_hook(supplied_http_client)
        else:
            sdk_client_kwargs["http_client"] = _metrics_http_client(
                timeout=sdk_client_kwargs.get("timeout")
            )

        # The hook is inactive unless collect_gateway_metrics() is active, so
        # one client serves both regular and metric-collecting calls. This also
        # preserves Langfuse's normal OpenAI SDK instrumentation.
        self.client = openai.AsyncOpenAI(**sdk_client_kwargs)

    @staticmethod
    def _record_gateway_metrics(
        collector: GatewayMetricsCollector, response: Any
    ) -> None:
        headers = _gateway_response_headers.get()
        if headers is None:
            raise GatewayMetricsError(
                "LLM gateway response headers were not captured for this request"
            )
        collector.record(headers, response)

    async def ainvoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.request_kwargs,
        }
        collector = _active_gateway_metrics.get()
        headers_token = _gateway_response_headers.set(None) if collector else None
        if output_model:
            kwargs["response_format"] = output_model
            try:
                response = await self.client.chat.completions.parse(**kwargs)
                if collector is not None:
                    self._record_gateway_metrics(collector, response)
                return LLMResponse(parsed=response.choices[0].message.parsed)
            finally:
                if headers_token is not None:
                    _gateway_response_headers.reset(headers_token)
        try:
            response = await self.client.chat.completions.create(**kwargs)
            if collector is not None:
                self._record_gateway_metrics(collector, response)
            return LLMResponse(parsed=response.choices[0].message.content)
        finally:
            if headers_token is not None:
                _gateway_response_headers.reset(headers_token)

    def invoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        """Synchronous wrapper around ainvoke."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            context = contextvars.copy_context()

            def run_in_worker() -> LLMResponse:
                return asyncio.run(self.ainvoke(prompt, output_model))

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(context.run, run_in_worker).result()
        return asyncio.run(self.ainvoke(prompt, output_model))
