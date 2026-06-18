"""Tests for the Pydantic AI-backed LLM wrapper.

Models are injected directly as the ``model`` argument (the wrapper hides its
``Agent``), exercising the ``_resolve_model`` "already a Model" branch. We use
``FunctionModel`` with a profile that advertises native JSON-schema output so the
``NativeOutput`` wrapping the wrapper applies is accepted.
"""

import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.profiles import ModelProfile

from themefinder.llm import LLM, LLMResponse, _resolve_model
from themefinder.models import Position, ThemeGenerationResponses


def _theme_json(label: str) -> str:
    return (
        '{"responses":[{"topic_label":"%s",'
        '"topic_description":"a description","position":"AGREEMENT"}]}' % label
    )


def native_model(label: str = "alpha") -> FunctionModel:
    """A FunctionModel that returns a fixed ThemeGenerationResponses tagged by label."""

    def fn(messages, info):
        return ModelResponse(parts=[TextPart(_theme_json(label))])

    return FunctionModel(fn, profile=ModelProfile(supports_json_schema_output=True))


def text_model(text: str = "hello") -> FunctionModel:
    def fn(messages, info):
        return ModelResponse(parts=[TextPart(text)])

    return FunctionModel(fn)


# --- _resolve_model / construction -------------------------------------------


@pytest.fixture()
def fake_openai_key(monkeypatch):
    """A dummy key so building an Agent over a bare "openai:" string succeeds."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


def test_direct_string_model_passed_through(fake_openai_key):
    """(a) A provider-prefixed string is passed straight to the Agent (direct mode)."""
    assert _resolve_model("openai:gpt-4o", None, None) == "openai:gpt-4o"
    llm = LLM("openai:gpt-4o")
    assert llm._model == "openai:gpt-4o"


def test_gateway_mode_builds_openai_chat_model():
    """(b) base_url+api_key builds an OpenAIChatModel over an OpenAIProvider, and
    needs no provider: prefix on the model name (LiteLLM-proxy mode)."""
    llm = LLM("gpt-4o", base_url="http://gateway.local/v1", api_key="secret")
    assert isinstance(llm._model, OpenAIChatModel)
    # The gateway model name carries no provider prefix.
    assert llm._model.model_name == "gpt-4o"


def test_api_key_only_also_uses_gateway_branch():
    llm = LLM("gpt-4o", api_key="secret")
    assert isinstance(llm._model, OpenAIChatModel)


def test_model_instance_passed_verbatim():
    """(c) A Model instance is used as-is (the test-injection seam)."""
    model = native_model()
    assert _resolve_model(model, None, None) is model
    assert LLM(model)._model is model


def test_temperature_builds_model_settings(fake_openai_key):
    llm = LLM("openai:gpt-4o", temperature=0)
    assert llm._settings is not None
    assert llm._settings["temperature"] == 0


def test_no_temperature_no_settings(fake_openai_key):
    assert LLM("openai:gpt-4o")._settings is None


# --- invoke / ainvoke --------------------------------------------------------


async def test_ainvoke_returns_llmresponse_with_parsed_model():
    """(d/e) ainvoke returns LLMResponse wrapping a parsed *Responses instance."""
    llm = LLM(native_model("transport"))
    result = await llm.ainvoke("prompt", output_model=ThemeGenerationResponses)
    assert isinstance(result, LLMResponse)
    assert isinstance(result.parsed, ThemeGenerationResponses)
    assert result.parsed.responses[0].topic_label == "transport"
    assert result.parsed.responses[0].position == Position.AGREEMENT


def test_invoke_sync_returns_llmresponse_with_parsed_model():
    llm = LLM(native_model("housing"))
    result = llm.invoke("prompt", output_model=ThemeGenerationResponses)
    assert isinstance(result.parsed, ThemeGenerationResponses)
    assert result.parsed.responses[0].topic_label == "housing"


async def test_ainvoke_without_output_model_returns_text():
    llm = LLM(text_model("plain text answer"))
    result = await llm.ainvoke("prompt")
    assert result.parsed == "plain text answer"


# --- multi-model path --------------------------------------------------------


async def test_same_input_through_two_models_yields_one_result_each():
    """(f) Running the same input through two different models yields one result
    per model — provider comparison needs no helper."""
    prompt = "same prompt"
    results = [
        await LLM(native_model(tag)).ainvoke(
            prompt, output_model=ThemeGenerationResponses
        )
        for tag in ("model_a", "model_b")
    ]
    labels = [r.parsed.responses[0].topic_label for r in results]
    assert labels == ["model_a", "model_b"]


def test_unknown_output_model_none_is_string_type():
    assert LLM._output_type(None) is str
