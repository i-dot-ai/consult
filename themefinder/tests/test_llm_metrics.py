"""Tests for evaluation metrics collected from LLM gateway responses."""

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from themefinder.llm import (
    GatewayMetricsError,
    OpenAILLM,
    _capture_gateway_response_headers,
    collect_gateway_metrics,
)


def _response(*, content: str = "answer", parsed=None, usage=None):
    message = SimpleNamespace(content=content, parsed=parsed)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def _llm(*, create=None, parse=None) -> OpenAILLM:
    def response_effect(response):
        responses = iter(response) if isinstance(response, list) else None

        async def call(**kwargs):
            result, headers = next(responses) if responses else response
            await _capture_gateway_response_headers(SimpleNamespace(headers=headers))
            return result

        return call

    llm = OpenAILLM(model="gateway-model", api_key="test-key")
    llm.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(side_effect=response_effect(create)),
                parse=AsyncMock(side_effect=response_effect(parse)),
            )
        )
    )
    return llm


def _headers(*, cost: str = "0.0015", duration_ms: str = "125") -> dict[str, str]:
    return {
        "x-litellm-response-cost": cost,
        "x-litellm-response-duration-ms": duration_ms,
    }


async def test_collects_and_sums_gateway_metrics_for_each_regular_call():
    first = (
        _response(
            usage=SimpleNamespace(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
        ),
        _headers(cost="0.0015", duration_ms="125"),
    )
    second = (
        _response(
            usage=SimpleNamespace(
                prompt_tokens=20, completion_tokens=7, total_tokens=27
            )
        ),
        _headers(cost="0.0025", duration_ms="375"),
    )
    llm = _llm(create=[first, second])

    with collect_gateway_metrics() as collector:
        assert (await llm.ainvoke("first")).parsed == "answer"
        assert (await llm.ainvoke("second")).parsed == "answer"

    summary = collector.summary()
    assert summary.call_count == 2
    assert summary.cost_usd == pytest.approx(0.004)
    assert summary.latency_seconds == 0.5
    assert summary.input_tokens == 30
    assert summary.output_tokens == 12
    assert summary.total_tokens == 42


async def test_collects_metrics_for_structured_calls():
    class Output(BaseModel):
        answer: str

    response = (
        _response(
            parsed=Output(answer="structured"),
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        ),
        _headers(cost="0.001", duration_ms="50"),
    )
    llm = _llm(parse=response)

    with collect_gateway_metrics() as collector:
        result = await llm.ainvoke("prompt", Output)

    assert result.parsed == Output(answer="structured")
    assert collector.summary().call_count == 1
    assert collector.summary().cost_usd == 0.001
    assert collector.summary().latency_seconds == 0.05


async def test_sync_invoke_copies_metric_context_to_its_worker_thread():
    response = (
        _response(
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        ),
        _headers(cost="0.001", duration_ms="50"),
    )
    llm = _llm(create=response)

    with collect_gateway_metrics() as collector:
        result = llm.invoke("prompt")

    assert result.parsed == "answer"
    assert collector.summary().call_count == 1
    assert collector.summary().cost_usd == 0.001


async def test_missing_gateway_metric_header_fails_instead_of_recording_zero():
    response = (
        _response(
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        ),
        {"x-litellm-response-cost": "0.001"},
    )
    llm = _llm(create=response)

    with (
        collect_gateway_metrics(),
        pytest.raises(GatewayMetricsError, match="x-litellm-response-duration-ms"),
    ):
        await llm.ainvoke("prompt")


async def test_uses_one_sdk_client_with_an_inactive_metrics_hook(monkeypatch):
    created_clients = []

    def create_client(**kwargs):
        created_clients.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr("themefinder.llm.openai.AsyncOpenAI", create_client)

    OpenAILLM(model="gateway-model")

    assert len(created_clients) == 1
    http_client = created_clients[0]["http_client"]
    assert _capture_gateway_response_headers in http_client.event_hooks["response"]
    await http_client.aclose()


async def test_langfuse_tracing_is_scoped_to_the_supplied_llm_instance():
    response = (
        _response(
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        ),
        _headers(),
    )
    generation = MagicMock()
    langfuse_client = MagicMock()
    langfuse_client.start_as_current_observation.return_value = nullcontext(generation)
    llm = _llm(create=response)
    llm.langfuse_client = langfuse_client

    await llm.ainvoke("prompt")
    await _llm(create=response).ainvoke("untraced prompt")

    langfuse_client.start_as_current_observation.assert_called_once_with(
        name="OpenAI-generation",
        as_type="generation",
        input=[{"role": "user", "content": "prompt"}],
        model="gateway-model",
    )
    generation.update.assert_called_once_with(
        output={"role": "assistant", "content": "answer"},
        usage_details={"input": 3, "output": 2, "total": 5},
    )


async def test_langfuse_observation_setup_failure_does_not_fail_llm_call():
    llm = _llm(create=(_response(), _headers()))
    llm.langfuse_client = MagicMock()
    llm.langfuse_client.start_as_current_observation.side_effect = RuntimeError()

    result = await llm.ainvoke("prompt")

    assert result.parsed == "answer"
